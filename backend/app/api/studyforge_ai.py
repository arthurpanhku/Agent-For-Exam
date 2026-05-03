"""StudyForge: variant questions and related AI helpers."""
import json
from typing import Literal

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.services.graph_service import GraphService
from app.services.conversation_service import ConversationService
from app.services.config_service import config_service
from app.services.study_enhancements import generate_variant_questions
from app.config import get_logger

router = APIRouter(prefix="/api/conversations", tags=["studyforge"])
logger = get_logger("app.studyforge_ai")


class VariantQuestionsRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=2000)
    mode: str = Field(default="mix", description="LightRAG query mode for context")
    count: int = Field(default=3, ge=1, le=10)
    base_difficulty: Literal["easy", "medium", "hard"] = "medium"


@router.post("/{conversation_id}/variant-questions")
async def create_variant_questions(conversation_id: str, body: VariantQuestionsRequest):
    """基于当前对话所属知识库检索摘录，生成带难度与布鲁姆层级的变式单选题。"""
    conv = ConversationService().get_conversation(conversation_id)
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="对话不存在")

    subject_id = conv.get("subject_id")
    rag_id = subject_id if subject_id else conversation_id

    gs = GraphService()
    if not gs.check_has_documents_fast(conversation_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="当前对话没有可用文档，无法生成与讲义绑定的变式题",
        )

    raw_pack = await gs.query_knowledge_raw(
        rag_id, body.topic, body.mode, context_id=conversation_id
    )
    excerpt = ""
    if raw_pack.get("status") == "success":
        excerpt = raw_pack.get("result") or ""
        rd = (raw_pack.get("raw_data") or {}).get("chunks") or []
        if rd:
            excerpt += "\n\n--- 片段 ---\n"
            for i, ch in enumerate(rd[:6]):
                if isinstance(ch, dict):
                    excerpt += f"\n[{i+1}] {ch.get('content', '')[:800]}\n"
    else:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=raw_pack.get("message") or "检索上下文失败",
        )

    chat_cfg = config_service.get_config("chat")
    model = chat_cfg.get("model", "")
    api_key = chat_cfg.get("api_key", "")
    host = chat_cfg.get("host", "")
    if not api_key or not host:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="聊天模型未配置，请在设置中填写 API Key 与模型",
        )

    questions, err = await generate_variant_questions(
        topic=body.topic,
        context_excerpt=excerpt,
        count=body.count,
        base_difficulty=body.base_difficulty,
        model=model,
        api_key=api_key,
        host=host,
    )
    if err:
        logger.warning("variant_questions_error", extra={"error": err})
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=err)

    return {
        "conversation_id": conversation_id,
        "topic": body.topic,
        "mode": body.mode,
        "questions": questions,
    }
