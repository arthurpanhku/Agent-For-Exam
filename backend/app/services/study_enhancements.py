"""StudyForge AI enhancements: citation trust, Socratic prompts, variant questions."""
from __future__ import annotations

import json
import re
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

import aiohttp

from app.config import get_logger

logger = get_logger("app.study_enhancements")

_TOKEN_RE = re.compile(r"[\u4e00-\u9fff]{2,}|\w{3,}")


def _tokens(text: str) -> set:
    if not text:
        return set()
    return {t.lower() for t in _TOKEN_RE.findall(text)}


def _jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def build_citation_analysis(raw_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Deterministic hints from graph query raw_data (entities, chunks)."""
    if not raw_data or not isinstance(raw_data, dict):
        return {
            "citations": [],
            "conflicts": [],
            "hints": ["当前检索未返回结构化图谱片段，无法计算引用可信度。"],
        }

    entities = raw_data.get("entities") or []
    chunks = raw_data.get("chunks") or []

    citations: List[Dict[str, Any]] = []
    for i, ch in enumerate(chunks[:12]):
        if not isinstance(ch, dict):
            continue
        content = (ch.get("content") or "")[:400]
        fid = ch.get("file_id")
        page = ch.get("page_index")
        toks = _tokens(content)
        trust = "high" if len(toks) > 25 and (fid and page) else "medium" if fid else "low"
        citations.append(
            {
                "rank": i + 1,
                "file_id": fid,
                "page": page,
                "trust": trust,
                "preview": (ch.get("content") or "")[:160].replace("\n", " "),
            }
        )

    conflicts: List[Dict[str, Any]] = []
    by_norm: Dict[str, List[dict]] = defaultdict(list)
    for ent in entities:
        if not isinstance(ent, dict):
            continue
        name = (ent.get("name") or "").strip().lower()
        if len(name) < 2:
            continue
        by_norm[name].append(ent)

    for name, group in by_norm.items():
        if len(group) < 2:
            continue
        file_ids = set()
        for g in group:
            for sd in g.get("source_documents") or []:
                if isinstance(sd, dict) and sd.get("file_id"):
                    file_ids.add(sd["file_id"])
        if len(file_ids) < 2:
            continue
        descs = [(g.get("description") or "")[:600] for g in group]
        neg_hits = [sum(1 for w in ("不是", "不正确", "错误", "不存在", "不会", "非") if w in d) for d in descs]
        pos_hits = [sum(1 for w in ("是", "正确", "存在", "可以", "能够") if w in d) for d in descs]
        j = _jaccard(_tokens(descs[0]), _tokens(descs[1])) if len(descs) >= 2 else 0.0
        reason = "duplicate_entity_across_documents"
        detail = "不同文档中出现同名实体，描述可能不一致，请回到原文核对。"
        if j > 0.12 and neg_hits and max(neg_hits) != min(neg_hits):
            reason = "possible_polarity_mismatch"
            detail = "同名实体在不同来源中的表述倾向不一致，存在潜在冲突，请对照原文。"

        conflicts.append(
            {
                "kind": reason,
                "entity_label": group[0].get("name") or name,
                "message": detail,
                "file_ids": list(file_ids)[:8],
            }
        )

    hints: List[str] = []
    if conflicts:
        hints.append(f"发现 {len(conflicts)} 处跨文档同名或表述差异，建议优先以 read 工具核对原文。")
    elif citations:
        hints.append("引用块已标注粗可信度：含明确 file_id+页码且文本较长者通常为 high。")
    else:
        hints.append("本次检索未返回可用文本块，可信度信息有限。")

    return {"citations": citations, "conflicts": conflicts, "hints": hints}


SOCRATIC_BLOCK = """
## 考我模式（苏格拉底式 · 与图谱强绑定）
- 用户希望被「考」而不是直接听结论：不要一上来给出完整标准答案或长篇推导终稿。
- **首轮必须**调用 `query_knowledge_graph`，`mode` 使用 `mix`，用用户主题做 query，以锁定教材/讲义在图谱与向量中的范围。
- 随后用 **1～2 个短问题** 引导用户自行思考；问题须显式关联图谱中可能出现的概念（可提示「结合你讲义中的某类定义」但不要编造页码）。
- 仅当用户明确说「公布答案」「揭晓」「给我标准答案」等时，才给出直接解答，并仍须遵守原有 `[[file_id|page]]` 与 References 规范。
- 若当前对话没有文档或工具返回提示无检索结果，诚实说明，并给出不依赖编造材料的一般思考方向。
"""


def augment_system_prompt_for_style(base: str, chat_style: str) -> str:
    if (chat_style or "").lower() == "socratic":
        return base.strip() + "\n\n" + SOCRATIC_BLOCK
    return base


async def generate_variant_questions(
    *,
    topic: str,
    context_excerpt: str,
    count: int,
    base_difficulty: str,
    model: str,
    api_key: str,
    host: str,
) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """Call chat LLM once to produce structured variant questions."""
    api_url = f"{host.rstrip('/')}/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    schema_hint = (
        '{"questions":[{"stem":"...","options":["A","B","C","D"],"answer":"A",'
        '"difficulty":"easy|medium|hard","bloom_level":"remember|understand|apply|analyze|evaluate|create",'
        '"rationale":"一句说明为何考查该点"}]}'
    )
    user = (
        f"主题: {topic}\n"
        f"难度基调: {base_difficulty}\n"
        f"需要题目数量: {count}\n"
        "下列为教材/检索摘录（可改写题干但不要编造未出现的事实）:\n"
        f"{context_excerpt[:6000]}\n"
        "只输出合法 JSON，键为 questions，数组元素字段必须齐全。"
    )
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是资深命题教师。根据给定主题与摘录生成单选题变式，"
                    "必须标注布鲁姆认知层级 bloom_level 与 difficulty。"
                    "输出严格 JSON，无 Markdown 围栏。"
                ),
            },
            {"role": "user", "content": user + "\nJSON 模板示例: " + schema_hint},
        ],
        "temperature": 0.65,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                api_url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=120)
            ) as resp:
                text = await resp.text()
                if resp.status != 200:
                    return [], f"LLM HTTP {resp.status}: {text[:500]}"
                data = json.loads(text)
                content = (data.get("choices") or [{}])[0].get("message", {}).get("content") or "{}"
                try:
                    parsed = json.loads(content)
                except json.JSONDecodeError:
                    m = re.search(r"\{[\s\S]*\}", content)
                    if not m:
                        return [], "模型未返回可解析 JSON"
                    parsed = json.loads(m.group(0))
                qs = parsed.get("questions") or []
                if not isinstance(qs, list):
                    return [], "模型返回格式异常"
                cleaned = []
                for q in qs[: max(count, 1)]:
                    if not isinstance(q, dict):
                        continue
                    cleaned.append(
                        {
                            "stem": str(q.get("stem", "")).strip(),
                            "options": [str(o) for o in (q.get("options") or [])][:6],
                            "answer": str(q.get("answer", "")).strip(),
                            "difficulty": str(q.get("difficulty", base_difficulty)).lower(),
                            "bloom_level": str(q.get("bloom_level", "understand")).lower(),
                            "rationale": str(q.get("rationale", "")).strip(),
                        }
                    )
                return cleaned, None
    except Exception as exc:  # pragma: no cover - network
        logger.exception("variant_questions_failed", extra={"error": str(exc)})
        return [], str(exc)
