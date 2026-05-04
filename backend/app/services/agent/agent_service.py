"""
Agent 核心服务模块

实现基于 LLM Function Calling 的智能 Agent 系统，支持多轮工具调用和流式响应。
conversation_id 会自动注入到所有工具调用中。
"""
import json
import time
from typing import Dict, List, Optional, AsyncIterator, Any

from app.services.agent.tool_registry import ToolRegistry
from app.services.agent.tool_executor import ToolExecutor
from app.services.agent.tools.mindmap_tool import MINDMAP_TOOL
from app.services.agent.tools.query_tool import QUERY_TOOL
from app.services.agent.tools.list_documents_tool import LIST_DOCUMENTS_TOOL
from app.services.agent.tools.read_tool import READ_TOOL
from app.services.conversation_service import ConversationService
from app.services.document_service import DocumentService
from app.services.lightrag_service import LightRAGService
from app.services.memory_service import MemoryService
from app.services.study_enhancements import augment_system_prompt_for_style, build_citation_analysis
import app.config as config
import aiohttp

logger = config.get_logger("app.agent")


def _normalize_tool_call(tool_call: Any) -> Optional[Dict]:
    """将单个 tool_call 规范化为标准格式，返回 None 表示无效。"""
    if not isinstance(tool_call, dict):
        return None

    tc_id = tool_call.get("id") or ""
    if not isinstance(tc_id, str):
        tc_id = str(tc_id)

    tc_type = tool_call.get("type", "function")
    if not isinstance(tc_type, str):
        tc_type = str(tc_type) if tc_type else "function"

    func = tool_call.get("function", {})
    if not isinstance(func, dict):
        return None

    name = func.get("name", "")
    if not isinstance(name, str):
        name = str(name) if name else ""
    if not name:
        return None

    args = func.get("arguments", "{}")
    if not isinstance(args, str):
        args = json.dumps(args, ensure_ascii=False) if isinstance(args, dict) else (str(args) if args is not None else "{}")

    if not tc_id:
        tc_id = f"call_{int(time.time() * 1000)}"

    return {"id": tc_id, "type": tc_type, "function": {"name": name, "arguments": args}}


def _normalize_tool_calls(tool_calls: List) -> List[Dict]:
    """过滤并规范化 tool_calls 列表。"""
    result = []
    for i, tc in enumerate(tool_calls):
        norm = _normalize_tool_call(tc)
        if norm:
            if not norm["id"]:
                norm["id"] = f"call_{i}_{int(time.time() * 1000)}"
            result.append(norm)
        else:
            logger.warning("跳过无效的 tool_call", extra={"event": "agent.invalid_tool_call", "index": i})
    return result


class AgentService:
    """Agent 核心服务"""

    def __init__(self):
        self.tool_registry = ToolRegistry()
        self.tool_executor = ToolExecutor(self.tool_registry)

        from app.services.agent.skill_manager import SkillManager
        self.skill_manager = SkillManager()
        self.skill_manager.discover_skills()

        self._register_default_tools()

    def _register_default_tools(self):
        self.tool_registry.register(MINDMAP_TOOL)
        self.tool_registry.register(QUERY_TOOL)
        self.tool_registry.register(LIST_DOCUMENTS_TOOL)
        self.tool_registry.register(READ_TOOL)

        logger.info(
            "Agent 服务初始化完成",
            extra={
                "event": "agent.init",
                "tool_count": len(self.tool_registry.tools),
                "skill_count": len(self.skill_manager._registry),
            },
        )

    def _build_document_context(self, conversation_id: str, max_documents: int = 30) -> str:
        """构建轻量文档上下文，减少为获取 filename/file_id 而调用 list_documents。"""
        try:
            conversation_service = ConversationService()
            document_service = DocumentService()
            conversation = conversation_service.get_conversation(conversation_id)
            subject_id = conversation.get("subject_id") if conversation else None

            if subject_id:
                documents = document_service.list_documents_for_subject(subject_id)
                scope_text = f"subject_id={subject_id}"
            else:
                documents = document_service.list_documents(conversation_id)
                scope_text = f"conversation_id={conversation_id}"

            if not documents:
                return "当前可用文档：无。"

            lines = [
                "当前可用文档（自动注入，优先使用此处的 filename 与 file_id；不要仅为了获取文档列表而调用 list_documents）：",
                f"范围：{scope_text}",
            ]

            visible_documents = documents[:max_documents]
            for index, doc in enumerate(visible_documents, 1):
                file_id = doc.get("file_id", "")
                filename = doc.get("filename", "未知文件")
                status = doc.get("status", "unknown")
                file_type = doc.get("file_type") or doc.get("file_extension") or ""
                lines.append(
                    f"{index}. file_id={file_id} | filename={filename} | status={status} | type={file_type}"
                )

            if len(documents) > max_documents:
                lines.append(
                    f"... 还有 {len(documents) - max_documents} 个文档未注入；如确需完整列表再调用 list_documents。"
                )

            return "\n".join(lines)
        except Exception as exc:
            logger.warning(
                "构建 Agent 文档上下文失败",
                extra={
                    "event": "agent.document_context_failed",
                    "conversation_id": conversation_id,
                    "error_message": str(exc),
                },
            )
            return "当前可用文档：读取失败；如任务需要文档列表，可调用 list_documents。"

    def _build_agent_system_prompt(self, document_context: str = "") -> str:
        """构建 Agent 系统提示词，自动注入技能元数据。"""
        tools_description = [f"- {tool.name}: {tool.description}" for tool in self.tool_registry.list_tools()]
        skills_snippet = self.skill_manager.get_system_prompt_snippet()

        return f"""你是一个智能助手，可以帮助用户完成各种任务。

你可以使用以下工具：
{chr(10).join(tools_description)}

{skills_snippet}

{document_context}

基本使用规则：
1. 根据用户的需求，智能选择合适的工具
2. 如果用户明确要求执行某个操作（如"生成思维导图"、"画脑图"等），使用 generate_mindmap 工具；若指名具体文档，优先使用上方自动注入的文档清单中的 file_id 作为 document_ids
3. 如果用户想要获取课程/讲义等文档中的事实性信息：
   - 若已知道大概位置（已知具体文档名/页码范围/很明确的页码线索），**直接使用 read 工具**读取原文
   - 若不知道大概位置，先使用 query_knowledge_graph **仅用于缩小范围与定位候选页码/关键词**，然后必须再用 read 工具读取原文确认
4. 如果用户想要查看文档列表（如"列出所有文档"、"显示文档"等），使用 list_documents 工具；其他场景优先使用自动注入的文档清单，只有清单为空、疑似过期或需要完整列表时才调用 list_documents
5. 如果用户要阅读某份文档的指定页码范围（如「读某文档第3页到第5页」），使用 read 工具，参数为文档名（filename）、起始页码（start_page）、终止页码（end_page）；文档名须与自动注入文档清单或 list_documents 返回的 filename 完全一致
6. 不要向用户透露工具名称，用自然语言描述操作 仅在必要时调用工具 如果任务简单或已知答案，直接回答，无需调用工具
7. **工具调用后，如果结果提示需要进一步操作，可以继续调用其他工具**
8. **只有在完成所有必要的工具调用后，才生成最终回答**
9. 工具调用后，将结果整合到回答中，以自然的方式呈现给用户

搜索和阅读原则:
- 与课程/讲义文档相关的事实性问题：
  - 若已知道大概位置（页码线索明确），直接 read 原文
  - 若不知道大概位置：先 query_knowledge_graph 缩小范围，再 read 原文确认细节
- 与课程/讲义无关的闲聊/常识类问题：不强制使用 query_knowledge_graph 或 read，可直接回答
- 不确定时先收集信息（搜索、读取文件等），优先通过工具获取信息，而非直接询问用户

参数使用原则:
- 仅在有相关工具时调用
- 确保提供必需参数，或可从上下文合理推断
- 如果缺少必需参数，询问用户
- 如果用户提供了具体值（如引号中的值），必须完全按该值使用
- 不要为可选参数编造值或询问

工具使用原则:
- 当用户提到"生成思维导图"、"生成脑图"、"画思维导图"等关键词时，必须使用 generate_mindmap 工具
- **conversation_id 参数会自动注入，你不需要也不应该在工具参数中提供 conversation_id**
- 调用工具时，只需要提供其他参数（如 document_ids、query、mode 等）
- 工具执行后，结果会自动返回给你，你需要用自然语言向用户解释结果

工具调用示例：
- 生成思维导图：调用 generate_mindmap，参数可以为空 {{}} 或指定文档 {{"document_ids": ["file_id1", "file_id2"]}}（不要包含 conversation_id）
  **重要：document_ids 必须使用 file_id（文档ID），而不是 filename（文件名）。优先从自动注入的文档清单获取 file_id。**
- 查询知识图谱：调用 query_knowledge_graph，参数 {{"query": "用户的问题", "mode": "mix"}}（不要包含 conversation_id）
- 阅读文档某几页：调用 read，参数 {{"filename": "文档名（与 list_documents 一致）", "start_page": 1, "end_page": 5}}（不要包含 conversation_id）


引用与信息来源标注规范

一、文档标识符说明
1. **file_id（文档ID）**：每个文档的唯一标识符，格式如 "abc123-def456-ghi789"
2. **filename（文件名）**：文档的显示名称，如 "01 - Introduction.pdf"
3. **重要**：
   - 在调用工具时（如 generate_mindmap），document_ids 参数必须使用 file_id，不能使用 filename
   - 如果不知道 file_id，先查看自动注入的文档清单；清单不可用时再调用 list_documents 工具查看文档列表

二、文档页面引用格式
当引用来自文档的具体页面或幻灯片时，必须在引用位置使用标准格式：`[[file_id|page_index]]`
- 格式说明：
  * `file_id`：文档的唯一标识符（通过 list_documents 工具获取）
  * `page_index`：页码或幻灯片编号，从 1 开始计数
- 示例：`根据文档内容 [[abc123-def456-ghi789|3]]，我们可以看到...`
- 重要：只能引用实际存在的文档和页码，不能编造 file_id 或页码

三、信息来源标注要求
1. 回答正文中的引用标记：
   - 所有来自工具结果的重要信息都要用方括号编号标记，如 `[1][[file_id|page_index]] `、`[2][[file_id|page_index]] `、`[3][[file_id|page_index]] `，按首次出现顺序递增
   - 同一信息如果依赖多个来源，可写成 `[1,2] [[file_id|page_index]] `
   - 知识图谱只可用于检索线索（定位范围/页码候选/关键词），不得作为事实依据；凡是需要引用的事实性结论，必须通过 read 读取原文并给出 `[[file_id|page_index]]`
2. 回答末尾的 References 部分：
   - 必须添加一个 **References** 部分，格式示例：
   ## References
   [1] [[file_id|page_index]] : 原文内容
   [2] [[file_id|page_index]] : 原文内容
3. 严格依据原文：
   - 事实性信息必须直接或间接来源于工具返回的数据，不能编造；
   - 如果在原始文档中未通过 read 找到对应原文，要明确说明"在当前文档中未找到相关内容"，不要自创答案或直接引用知识图谱内容。

四、格式检查清单
在生成最终回答前，请确认：
- 正文中所有来源于文档的信息都有引用编号 `[X] [[file_id|page_index]]`
- 是否没有双中括号 [[...|...]]，而是单中括号 [file_id|page] !!!
- 末尾有完整的 References 部分
- 每个引用都包含了可追溯的原文内容
- 对于数学公式, 行内公式用 $...$ 块级公式用 $$...$$
"""

    async def process_user_query(
        self,
        conversation_id: str,
        user_query: str,
        conversation_history: Optional[List[Dict]] = None,
        max_rounds: int = 15,
        *,
        chat_style: str = "default",
        include_citation_analysis: bool = True,
    ) -> AsyncIterator[Dict[str, Any]]:
        """处理用户查询（Agent模式，支持多轮工具调用）

        Yields:
            流式响应数据
        """
        functions = self.tool_registry.to_function_calling_format()

        document_context = self._build_document_context(conversation_id)
        system_prompt = augment_system_prompt_for_style(
            self._build_agent_system_prompt(document_context=document_context),
            chat_style,
        )
        last_kg_raw: Optional[Dict[str, Any]] = None

        if conversation_history is None:
            memory_service = MemoryService()
            conversation_history = memory_service.get_recent_history(
                conversation_id,
                max_turns=3,
                max_tokens_per_message=500,
            )

        current_messages: List[Dict] = []
        if conversation_history:
            current_messages.extend(conversation_history)
        current_messages.append({"role": "user", "content": user_query})

        for round_count in range(1, max_rounds + 1):
            logger.info(
                "开始新一轮工具调用",
                extra={
                    "event": "agent.round_start",
                    "conversation_id": conversation_id,
                    "round": round_count,
                    "message_count": len(current_messages),
                },
            )

            tool_calls_buffer: List[Dict] = []
            accumulated_content = ""
            has_tool_calls = False

            async for chunk in self._call_llm_with_tools_round(
                conversation_id, system_prompt, current_messages, functions
            ):
                if chunk.get("type") == "tool_call":
                    tool_calls_buffer.append(chunk.get("tool_call"))
                    has_tool_calls = True
                    yield chunk
                elif chunk.get("type") == "response":
                    accumulated_content += chunk.get("content", "")
                    yield chunk
                else:
                    yield chunk

            if not has_tool_calls or not tool_calls_buffer:
                logger.info(
                    "无工具调用，结束循环",
                    extra={"event": "agent.no_more_tools", "conversation_id": conversation_id, "round": round_count},
                )
                break

            validated_tool_calls = _normalize_tool_calls(tool_calls_buffer)

            current_messages.append({
                "role": "assistant",
                "content": accumulated_content or "",
                "tool_calls": validated_tool_calls,
            })

            tool_results: List[Dict] = []
            tool_call_index = 0

            async for result in self._execute_tool_calls(validated_tool_calls, conversation_id):
                yield result

                if result.get("type") == "tool_result" and result.get("tool_name") == "query_knowledge_graph":
                    extracted = self._extract_kg_raw_from_tool_result(result)
                    if extracted is not None:
                        last_kg_raw = extracted

                if result["type"] == "tool_result":
                    tool_results.append(result)
                    tc_id = validated_tool_calls[tool_call_index]["id"] if tool_call_index < len(validated_tool_calls) else ""
                    current_messages.append({
                        "role": "tool",
                        "content": self._format_tool_result(result.get("result", {})),
                        "tool_call_id": tc_id,
                    })
                    tool_call_index += 1
                elif result["type"] == "tool_error":
                    tc_id = validated_tool_calls[tool_call_index]["id"] if tool_call_index < len(validated_tool_calls) else ""
                    current_messages.append({
                        "role": "tool",
                        "content": f"工具执行失败: {result.get('message', '')}",
                        "tool_call_id": tc_id,
                    })
                    tool_results.append(result)
                    tool_call_index += 1

            if not tool_results:
                logger.warning(
                    "无工具执行结果，结束循环",
                    extra={"event": "agent.no_tool_results", "conversation_id": conversation_id, "round": round_count},
                )
                break
        else:
            # for-else: loop exhausted max_rounds without break
            logger.warning(
                "达到最大工具调用轮次限制",
                extra={"event": "agent.max_rounds_reached", "conversation_id": conversation_id, "max_rounds": max_rounds},
            )
            yield {"type": "error", "content": f"达到最大工具调用轮次限制 ({max_rounds} 轮)，请简化您的请求"}
            return

        if include_citation_analysis and last_kg_raw is not None:
            yield {"type": "citation_analysis", "content": build_citation_analysis(last_kg_raw)}

    def _extract_kg_raw_from_tool_result(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """从 query_knowledge_graph 工具结果中取出 raw_data。"""
        ex = item.get("result")
        if not isinstance(ex, dict):
            return None
        inner = ex.get("result")
        if isinstance(inner, dict) and inner.get("raw_data") is not None:
            rd = inner.get("raw_data")
            return rd if isinstance(rd, dict) else None
        rd = ex.get("raw_data")
        return rd if isinstance(rd, dict) else None

    async def _call_llm_with_tools_round(
        self,
        conversation_id: str,
        system_prompt: str,
        messages: List[Dict],
        functions: List[Dict],
    ) -> AsyncIterator[Dict[str, Any]]:
        """单轮 LLM 调用（支持 Function Calling 和流式响应）。"""
        llm_messages: List[Dict] = [{"role": "system", "content": system_prompt}]

        for msg in messages:
            cleaned = msg.copy()
            role = cleaned.get("role")

            # 规范化 content 字段
            content = cleaned.get("content")
            if content is None:
                cleaned["content"] = ""
            elif not isinstance(content, str):
                cleaned["content"] = str(content)

            # tool 消息必须有 tool_call_id
            if role == "tool":
                if not cleaned.get("tool_call_id"):
                    continue

            # assistant 消息的 tool_calls 规范化
            if role == "assistant" and "tool_calls" in cleaned:
                tcs = cleaned.get("tool_calls", [])
                if isinstance(tcs, list) and tcs:
                    valid = _normalize_tool_calls(tcs)
                    if valid:
                        cleaned["tool_calls"] = valid
                    else:
                        cleaned.pop("tool_calls", None)
                else:
                    cleaned.pop("tool_calls", None)

            llm_messages.append(cleaned)

        logger.debug(
            "发送 LLM 请求",
            extra={
                "event": "agent.llm_request",
                "conversation_id": conversation_id,
                "message_count": len(llm_messages),
            },
        )

        from app.services.config_service import config_service
        chat_config = config_service.get_config("chat")
        model = chat_config.get("model", config.settings.chat_llm_model)
        api_key = chat_config.get("api_key", config.settings.chat_llm_binding_api_key)
        host = chat_config.get("host", config.settings.chat_llm_binding_host)

        api_url = f"{host}/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

        payload: Dict[str, Any] = {
            "model": model,
            "messages": llm_messages,
            "stream": True,
            "temperature": 0.7,
        }
        if functions:
            payload["tools"] = functions
            payload["tool_choice"] = "auto"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    api_url,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=300),
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        if response.status == 401:
                            error_msg = "API Key 无效或已过期，请在设置中检查并更新 API Key"
                        else:
                            error_msg = f"LLM API 错误: {response.status}"
                        logger.error("LLM API 错误", extra={"event": "agent.llm_error", "status": response.status, "conversation_id": conversation_id})
                        yield {"type": "error", "content": error_msg}
                        return

                    tool_calls_buffer: List[Dict] = []
                    finished_tool_calls = False
                    yielded_indices: set = set()

                    async for line in response.content:
                        if not line:
                            continue

                        line_text = line.decode("utf-8")
                        for chunk in line_text.split("\n"):
                            if not chunk.strip() or chunk.startswith(":"):
                                continue
                            if chunk.startswith("data: "):
                                chunk = chunk[6:]
                            if chunk.strip() == "[DONE]":
                                if tool_calls_buffer and not finished_tool_calls:
                                    finished_tool_calls = True
                                    for i, tc in enumerate(tool_calls_buffer):
                                        if tc.get("function", {}).get("name") and i not in yielded_indices:
                                            if not tc.get("id"):
                                                tc["id"] = f"call_{i}_{int(time.time() * 1000)}"
                                            yielded_indices.add(i)
                                            yield {"type": "tool_call", "tool_call": tc}
                                return

                            try:
                                data = json.loads(chunk)
                            except json.JSONDecodeError:
                                continue

                            choices = data.get("choices", [])
                            if not choices:
                                continue
                            delta = choices[0].get("delta", {})

                            if "tool_calls" in delta and delta["tool_calls"]:
                                for tc_delta in delta["tool_calls"]:
                                    idx = tc_delta.get("index", 0)
                                    while len(tool_calls_buffer) <= idx:
                                        tool_calls_buffer.append({"id": "", "type": "function", "function": {"name": "", "arguments": ""}})
                                    tc = tool_calls_buffer[idx]

                                    if "id" in tc_delta:
                                        tc["id"] = tc_delta["id"]

                                    if "function" in tc_delta:
                                        fd = tc_delta["function"]
                                        if fd.get("name"):
                                            tc["function"]["name"] = fd["name"]
                                            if idx not in yielded_indices:
                                                if not tc.get("id"):
                                                    tc["id"] = f"call_{idx}_{int(time.time() * 1000)}"
                                                yielded_indices.add(idx)
                                                yield {"type": "tool_call", "tool_call": tc.copy()}
                                        if fd.get("arguments"):
                                            tc["function"]["arguments"] += fd["arguments"]
                                            if tc["function"]["name"] and idx not in yielded_indices:
                                                if not tc.get("id"):
                                                    tc["id"] = f"call_{idx}_{int(time.time() * 1000)}"
                                                yielded_indices.add(idx)
                                                yield {"type": "tool_call", "tool_call": tc.copy()}

                            if delta.get("content"):
                                yield {"type": "response", "content": delta["content"]}

                    # 流结束后补发未 yield 的 tool_calls
                    if tool_calls_buffer and not finished_tool_calls:
                        for i, tc in enumerate(tool_calls_buffer):
                            if tc.get("function", {}).get("name") and i not in yielded_indices:
                                if not tc.get("id"):
                                    tc["id"] = f"call_{i}_{int(time.time() * 1000)}"
                                yield {"type": "tool_call", "tool_call": tc}
                                yielded_indices.add(i)

        except Exception as e:
            logger.exception("调用 LLM 时出错", extra={"event": "agent.llm_exception", "conversation_id": conversation_id})
            yield {"type": "error", "content": f"调用 LLM 时出错: {str(e)}"}

    def _format_tool_result(self, result_data: Dict[str, Any]) -> str:
        """格式化工具执行结果为字符串，用于发送回 LLM。"""
        status = result_data.get("status", "unknown")

        # 区分生成器工具（直接包含结果字段）和普通工具（result 嵌套）
        if "result" in result_data and isinstance(result_data.get("result"), dict):
            tool_result = result_data["result"]
        else:
            tool_result = result_data

        if status == "success":
            if not isinstance(tool_result, dict):
                return f"执行成功。结果：{str(tool_result)}"

            message = tool_result.get("message", "执行成功")
            body_content = tool_result.get("content", "")
            result_content = tool_result.get("result", "")
            mindmap_content = tool_result.get("mindmap_content", "")

            formatted = f"执行成功。{message}" if message else "执行成功。"
            if body_content:
                formatted += f"\n\n内容：\n{body_content}" if isinstance(body_content, str) else f"\n\n内容：{str(body_content)}"
            elif result_content:
                formatted += f"\n\n查询结果：\n{result_content}" if isinstance(result_content, str) else f"\n\n结果：{str(result_content)}"
            elif mindmap_content:
                formatted += "\n\n思维脑图已生成，内容已保存。任务已完成，无需再次调用此工具。"
            return formatted

        elif status == "error":
            error_msg = result_data.get("message") or tool_result.get("message", "执行失败")
            error_detail = result_data.get("error") or tool_result.get("error", "")
            return f"执行失败：{error_msg}\n错误详情：{error_detail}" if error_detail else f"执行失败：{error_msg}"

        return f"执行状态：{status}\n结果：{json.dumps(result_data, ensure_ascii=False)}"

    async def _execute_tool_calls(
        self,
        tool_calls: List[Dict],
        conversation_id: str,
    ) -> AsyncIterator[Dict[str, Any]]:
        """执行工具调用列表。"""
        for tool_call in tool_calls:
            func = tool_call.get("function", {})
            tool_name = func.get("name", "")
            if not tool_name:
                continue

            arguments_str = func.get("arguments") or "{}"
            if not arguments_str.strip():
                arguments_str = "{}"

            try:
                arguments = json.loads(arguments_str)
            except json.JSONDecodeError as e:
                yield {
                    "type": "tool_error",
                    "tool_name": tool_name,
                    "message": f"工具参数解析失败: {arguments_str}, 错误: {str(e)}",
                }
                continue

            if self.tool_executor.is_generator_tool(tool_name):
                async for item in self.tool_executor.execute_generator(tool_name, arguments, conversation_id):
                    if item["type"] == "tool_progress":
                        yield item
                    elif item["type"] == "tool_result":
                        yield {
                            "type": "tool_result",
                            "tool_name": tool_name,
                            "arguments": arguments,
                            "result": item["result"],
                        }
                        if tool_name == "generate_mindmap" and item["result"].get("status") == "success":
                            mc = item["result"].get("mindmap_content")
                            if mc:
                                yield {"type": "mindmap_content", "content": mc}
            else:
                result = await self.tool_executor.execute(tool_name, arguments, conversation_id)
                yield {
                    "type": "tool_result",
                    "tool_name": tool_name,
                    "arguments": arguments,
                    "result": result,
                }
                if tool_name == "generate_mindmap" and result.get("status") == "success":
                    mc = result.get("result", {}).get("mindmap_content")
                    if mc:
                        yield {"type": "mindmap_content", "content": mc}
