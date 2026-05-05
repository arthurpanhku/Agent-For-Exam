"""Orchestrator：扫描对话所选试卷，按试卷串行执行「题目分批 + Sub 派发」并写入轨迹；分析完成后生成报告"""
import asyncio
from typing import Any, Dict, List

from app.services.conversation_service import ConversationService
from app.services.exam.exam_storage import ExamStorage
from app.services.graph_service import GraphService
from app.services.exam_analysis.event_bus import emit as event_emit
from app.services.exam_analysis.hooks import default_hooks
from app.services.exam_analysis.sub_agent import run_sub_agent
from app.services.exam_analysis.sub_agent import ERROR_INDEX_INCOMPLETE
from app.services.exam_analysis.trace_storage import TraceStorage
from app.services.exam_analysis.report_aggregation import build_report

MAX_CONCURRENT_SUBS = 2
DEFAULT_BATCH_SIZE = 5


def _flatten_questions(questions: List[Any]) -> List[Dict[str, Any]]:
    """将题目列表（含子题）展平为 [{id, content, ...}, ...]。"""
    out: List[Dict[str, Any]] = []

    def add(q: Any) -> None:
        sub = getattr(q, "sub_questions", None) or []
        if sub:
            for s in sub:
                add(s)
        else:
            out.append({"id": getattr(q, "id", ""), "content": getattr(q, "content", ""), "index": getattr(q, "index", 0)})

    for q in questions:
        add(q)
    return out


async def _run_exam_mapping(
    conversation_id: str,
    subject_id: str,
    exam_id: str,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> List[Dict[str, Any]]:
    """
    Orchestrator 内部逻辑：拉取该试卷题目、按批派发 Sub、写轨迹与事件。
    原 Lead Agent 职责已收敛于此，不再单独模块。
    """
    storage = ExamStorage()
    exam = storage.get_exam(exam_id)
    if not exam or not exam.questions:
        return []
    questions_data = _flatten_questions(exam.questions)
    if not questions_data:
        return []
    year = getattr(exam, "year", None) or ""
    label = f"年份 Lead · {year}"
    lead_id = f"lead-{exam_id}"
    lead_trace: Dict[str, Any] = {
        "agent_id": lead_id,
        "role": "lead",
        "label": label,
        "status": "running",
        "thinking_blocks": [{"title": "任务规划", "content": f"试卷 {exam_id} 共 {len(questions_data)} 题，按每 {batch_size} 题一批派发 Sub。", "sequence": 0}],
        "tool_calls": [],
        "updated_at": None,
    }
    default_hooks.agents.on_lead_start(conversation_id, lead_trace)
    sem = asyncio.Semaphore(MAX_CONCURRENT_SUBS)
    append_lock = asyncio.Lock()
    batch_starts = list(range(0, len(questions_data), batch_size))
    default_hooks.pipeline.on_pipeline_exam_start(
        conversation_id,
        subject_id,
        exam_id,
        total_questions=len(questions_data),
        batch_size=batch_size,
    )

    def _emit(ev: Dict[str, Any]) -> None:
        event_emit(conversation_id, ev)

    async def run_batch(start_i: int) -> Dict[str, Any]:
        batch = questions_data[start_i : start_i + batch_size]
        sub_id = f"sub-{exam_id}-{start_i // batch_size}"
        sub_label = f"题目  · {batch[0]['id']}-{batch[-1]['id']}"
        sub_placeholder = {
            "agent_id": sub_id,
            "role": "sub",
            "label": sub_label,
            "lead_id": lead_id,
            "status": "running",
            "thinking_blocks": [],
            "tool_calls": [],
            "updated_at": None,
        }
        async with append_lock:
            default_hooks.agents.on_subagent_start(conversation_id, sub_placeholder)
        async with sem:
            sub_trace = await run_sub_agent(
                subject_id=subject_id,
                conversation_id=conversation_id,
                exam_id=exam_id,
                question_batch=batch,
                agent_id=sub_id,
                label=sub_label,
                lead_id=lead_id,
                emit=_emit,
            )
        async with append_lock:
            default_hooks.agents.on_subagent_end(conversation_id, sub_trace)
        return sub_trace

    sub_traces = await asyncio.gather(*[run_batch(i) for i in batch_starts])
    success = not any(trace.get("status") == "failed" for trace in sub_traces)

    lead_done: Dict[str, Any] = {
        "agent_id": f"{lead_id}-done",
        "role": "lead",
        "label": label + (" · 完成" if success else " · 部分失败"),
        "status": "done" if success else "failed",
        "thinking_blocks": [{"title": "完成" if success else "部分失败", "content": f"试卷 {exam_id} 已处理完毕。", "sequence": 0}],
        "tool_calls": [],
        "updated_at": None,
    }
    default_hooks.agents.on_lead_end(conversation_id, lead_done)
    default_hooks.pipeline.on_pipeline_exam_end(conversation_id, subject_id, exam_id, success)
    return sub_traces


def _subject_index_status(subject_id: str) -> Dict[str, Any]:
    from app.services.document_service import DocumentService

    doc_service = DocumentService()
    documents = doc_service.list_documents_for_subject(subject_id)
    total = len(documents)
    completed = len([doc for doc in documents if doc.get("status") == "completed"])
    incomplete = [
        {"file_id": doc.get("file_id"), "filename": doc.get("filename"), "status": doc.get("status")}
        for doc in documents
        if doc.get("status") != "completed"
    ]
    return {
        "ready": total > 0 and completed == total,
        "total": total,
        "completed": completed,
        "incomplete": incomplete,
    }


async def run_analysis(conversation_id: str) -> None:
    """
    读取对话的 subject_id、selected_exam_ids；
    为该 subject 构建实体页码映射；
    对每个 exam_id 串行执行「题目分批 + Sub 派发」（_run_exam_mapping，原 Lead 逻辑已收敛于此）；
    轨迹由本模块与 Sub 写入；
    分析完成后生成报告并写入 report.json；开始时删除旧报告缓存。
    """
    from app.services.exam_analysis.event_bus import wait_for_subscriber
    TraceStorage.delete_report(conversation_id)
    conv_svc = ConversationService()
    conversation = conv_svc.get_conversation(conversation_id)
    if not conversation:
        return
    subject_id = conversation.get("subject_id")
    selected_exam_ids = list(dict.fromkeys(conversation.get("selected_exam_ids") or []))
    if not subject_id or not selected_exam_ids:
        return
    default_hooks.pipeline.on_pipeline_start(conversation_id, subject_id, selected_exam_ids)
    await wait_for_subscriber(conversation_id)
    event_emit(conversation_id, {"type": "analysis_started", "conversation_id": conversation_id})
    index_status = _subject_index_status(subject_id)
    if not index_status["ready"]:
        error_event = {
            "type": "analysis_error",
            "conversation_id": conversation_id,
            "error_type": ERROR_INDEX_INCOMPLETE,
            "message": "请先完成文档索引后再启动试题分析",
            "index_status": index_status,
        }
        event_emit(conversation_id, error_event)
        TraceStorage.append_trace(conversation_id, {
            "agent_id": "pipeline-index-check",
            "role": "pipeline",
            "label": "索引检查",
            "status": "failed",
            "error_type": ERROR_INDEX_INCOMPLETE,
            "thinking_blocks": [{
                "title": "索引未完成",
                "content": error_event["message"],
                "error_type": ERROR_INDEX_INCOMPLETE,
                "sequence": 0,
            }],
            "tool_calls": [],
            "updated_at": None,
        })
        default_hooks.pipeline.on_pipeline_end(conversation_id, False)
        event_emit(conversation_id, {"type": "stream_end"})
        return
    graph = GraphService()
    await graph.build_entity_page_mapping(subject_id)
    all_sub_traces: List[Dict[str, Any]] = []
    for exam_id in selected_exam_ids:
        sub_traces = await _run_exam_mapping(conversation_id=conversation_id, subject_id=subject_id, exam_id=exam_id, batch_size=DEFAULT_BATCH_SIZE)
        all_sub_traces.extend(sub_traces)
    success = not any(trace.get("status") == "failed" for trace in all_sub_traces)
    default_hooks.pipeline.on_pipeline_end(conversation_id, success)
    if success:
        event_emit(conversation_id, {"type": "analysis_done"})
    else:
        failed = next((trace for trace in all_sub_traces if trace.get("status") == "failed"), {})
        event_emit(conversation_id, {
            "type": "analysis_error",
            "conversation_id": conversation_id,
            "error_type": failed.get("error_type") or "unknown",
            "message": "试题分析未完整完成",
        })
    report = build_report(conversation_id)
    if report and success:
        TraceStorage.save_report(conversation_id, report)
        default_hooks.pipeline.on_report_saved(conversation_id, {"has_report": True})
    event_emit(conversation_id, {"type": "stream_end"})
