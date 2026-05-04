"""文档服务，处理文档上传、解析、LightRAG 集成"""
import asyncio
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from fastapi import UploadFile

import app.config as config
from app.services.conversation_service import ConversationService
from app.services.lightrag_service import LightRAGService
from app.services.mindmap_service import MindMapService
from app.storage.file_manager import FileManager
from app.utils.document_parser import DocumentParser

logger = config.get_logger("app.document_service")

# 全局信号量：限制同时处理的文档数量（避免 LightRAG 并发冲突）
_processing_semaphore = asyncio.Semaphore(1)
# 思维脑图信号量：确保同一对话的思维脑图串行生成
_mindmap_semaphore: Dict[str, asyncio.Semaphore] = {}
_mindmap_lock = asyncio.Lock()
# 处理队列锁
_queue_lock = asyncio.Lock()
_processing_queue: Dict[str, List[str]] = {}


class DocumentService:
    """文档服务"""

    def __init__(self):
        self.conversation_service = ConversationService()
        self.lightrag_service = LightRAGService()
        self.mindmap_service = MindMapService()
        self.file_manager = FileManager()
        self.document_parser = DocumentParser()
        self.status_dir = Path(config.settings.conversations_metadata_dir) / "document_status"
        self.status_dir.mkdir(parents=True, exist_ok=True)

    # ── 内部共用实现 ──────────────────────────────────────────────────────────

    def _clean_base64_text(self, text: str, base64_file: Path) -> Tuple[str, Dict[str, str]]:
        """清理文本中的 base64 字符串，追加写入 base64_file，返回清理后文本和映射。"""
        base64_map: Dict[str, str] = {}
        if base64_file.exists():
            try:
                with open(base64_file, "r", encoding="utf-8") as f:
                    existing = json.load(f)
                    base64_map = existing if isinstance(existing, dict) else {}
            except Exception:
                base64_map = {}

        existing_indices = [int(k) for k in base64_map.keys() if k.isdigit()]
        next_index = max(existing_indices, default=0) + 1
        cleaned_text = text

        latexit_pattern = r"<latexit[^>]*>([^<]*)</latexit>"

        def replace_latexit(match):
            nonlocal next_index
            full_match = match.group(0)
            tag_content = match.group(1).strip()
            sha1_match = re.search(r'sha1_base64="([^"]+)"', full_match)
            b64_in_content = re.search(r"[A-Za-z0-9+/=]{50,}", tag_content)
            if b64_in_content:
                value = b64_in_content.group(0)
            elif sha1_match:
                value = sha1_match.group(1)
            elif tag_content and len(tag_content) > 20:
                value = tag_content
            else:
                return ""
            idx = str(next_index)
            base64_map[idx] = value
            next_index += 1
            return f"[BASE64_{idx}]"

        cleaned_text = re.sub(latexit_pattern, replace_latexit, cleaned_text, flags=re.DOTALL)

        standalone_pattern = r"(?<!\[BASE64_)[A-Za-z0-9+/=]{50,}(?!\])"

        def replace_standalone(match):
            nonlocal next_index
            b64 = match.group(0)
            if re.match(r"^[A-Za-z0-9+/=]+$", b64):
                idx = str(next_index)
                base64_map[idx] = b64
                next_index += 1
                return f"[BASE64_{idx}]"
            return b64

        cleaned_text = re.sub(standalone_pattern, replace_standalone, cleaned_text)

        if base64_map:
            base64_file.parent.mkdir(parents=True, exist_ok=True)
            with open(base64_file, "w", encoding="utf-8") as f:
                json.dump(base64_map, f, ensure_ascii=False, indent=2)

        return cleaned_text, base64_map

    async def _build_page_index_json_impl(
        self,
        namespace_id: str,
        document_id: str,
        file_path: str,
        index_dir: Path,
        *,
        filename: Optional[str] = None,
    ) -> None:
        """构建并保存 page_index JSON 的共用实现。"""
        try:
            logger.info("开始构建页级索引", extra={"event": "doc.page_index_start", "document_id": document_id[:8]})
            file_ext = Path(file_path).suffix.lower()
            pages: List = []

            if file_ext == ".pdf":
                from app.utils.pdf_parser import PDFParser
                pages = PDFParser().extract_pages(file_path, file_id=document_id)
            elif file_ext in (".ppt", ".pptx"):
                from app.utils.ppt_parser import PPTParser
                pages = PPTParser().extract_pages(file_path, file_id=document_id)
            else:
                logger.warning("不支持构建页级索引的文件类型", extra={"event": "doc.page_index_unsupported", "ext": file_ext})
                return

            if not pages:
                logger.warning("文档未提取到任何页面", extra={"event": "doc.page_index_empty", "document_id": document_id[:8]})
                return

            resolved_filename = filename or Path(file_path).name
            page_index_data = {
                "document_id": document_id,
                "filename": resolved_filename,
                "pages": pages,
            }

            index_dir.mkdir(parents=True, exist_ok=True)
            page_index_file = index_dir / f"{document_id}.json"
            with open(page_index_file, "w", encoding="utf-8") as f:
                json.dump(page_index_data, f, ensure_ascii=False, indent=2)

            logger.info("页级索引构建完成", extra={"event": "doc.page_index_done", "path": str(page_index_file)})
        except Exception as e:
            logger.error("构建页级索引失败", extra={"event": "doc.page_index_error", "document_id": document_id[:8], "error": str(e)})

    async def _process_document_impl(
        self,
        namespace_id: str,
        document_id: str,
        file_path: str,
        base64_file: Path,
        page_index_dir: Path,
        status_loader,
        status_saver,
        filename: Optional[str] = None,
    ) -> None:
        """文档处理的共用核心实现（解析 → 清理 → 页级索引 → LightRAG → 实体映射）。"""
        status_loader_result = status_loader()
        if document_id in status_loader_result.get("documents", {}):
            status_loader_result["documents"][document_id]["status"] = "processing"
            status_saver(status_loader_result)

        try:
            fp = Path(file_path)
            if not fp.exists():
                raise FileNotFoundError(f"文件不存在: {document_id}")

            text = self.document_parser.extract_text(str(fp), file_id=document_id)
            if not text or not text.strip():
                raise ValueError("文档解析后文本内容为空")

            cleaned_text, _ = self._clean_base64_text(text, base64_file)

            await self._build_page_index_json_impl(
                namespace_id, document_id, str(fp), page_index_dir, filename=filename
            )

            logger.info("开始生成知识图谱", extra={"event": "doc.kg_start", "document_id": document_id[:8]})
            track_id = await self.lightrag_service.insert_document(
                conversation_id=namespace_id,
                text=cleaned_text,
                doc_id=document_id,
            )

            st = status_loader()
            if document_id in st.get("documents", {}):
                st["documents"][document_id]["status"] = "completed"
                st["documents"][document_id]["lightrag_track_id"] = track_id
                status_saver(st)

            try:
                from app.services.graph_service import GraphService
                await GraphService().build_entity_page_mapping(namespace_id, document_ids=[document_id])
            except Exception as e:
                logger.warning("实体页码映射更新失败", extra={"event": "doc.entity_mapping_failed", "error": str(e)})

            logger.info("文档处理完成", extra={"event": "doc.process_done", "document_id": document_id[:8]})

        except Exception as e:
            st = status_loader()
            if document_id in st.get("documents", {}):
                st["documents"][document_id]["status"] = "failed"
                st["documents"][document_id]["error"] = str(e)
                status_saver(st)
            logger.error("文档处理失败", extra={"event": "doc.process_error", "document_id": document_id[:8], "error": str(e)})
            raise

    # ── 状态文件 I/O（conversation 维度）────────────────────────────────────

    def _get_status_file(self, conversation_id: str) -> Path:
        return self.status_dir / f"{conversation_id}.json"

    def _load_status(self, conversation_id: str) -> Dict:
        status_file = self._get_status_file(conversation_id)
        if status_file.exists():
            try:
                with open(status_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {"documents": {}}
        return {"documents": {}}

    def _save_status(self, conversation_id: str, status: Dict):
        with open(self._get_status_file(conversation_id), "w", encoding="utf-8") as f:
            json.dump(status, f, ensure_ascii=False, indent=2)

    # ── 状态文件 I/O（subject 维度）─────────────────────────────────────────

    def _get_subject_status_file(self, subject_id: str) -> Path:
        d = Path(config.settings.conversations_metadata_dir) / "subjects" / subject_id
        d.mkdir(parents=True, exist_ok=True)
        return d / "documents.json"

    def _load_subject_status(self, subject_id: str) -> Dict:
        status_file = self._get_subject_status_file(subject_id)
        if status_file.exists():
            try:
                with open(status_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {"documents": {}}
        return {"documents": {}}

    def _save_subject_status(self, subject_id: str, status: Dict):
        with open(self._get_subject_status_file(subject_id), "w", encoding="utf-8") as f:
            json.dump(status, f, ensure_ascii=False, indent=2)

    # ── 文件校验 ─────────────────────────────────────────────────────────────

    def _validate_file(self, filename: str) -> Tuple[bool, Optional[str]]:
        ext = Path(filename).suffix.lower().lstrip(".")
        if ext not in config.settings.allowed_extensions:
            return False, f"不支持的文件类型: {ext}，仅支持 {', '.join(config.settings.allowed_extensions)}"
        return True, None

    async def _check_file_size(self, file_content: bytes) -> Tuple[bool, Optional[str]]:
        size = len(file_content)
        if size > config.settings.max_file_size:
            return False, f"文件大小 {size / 1024 / 1024:.2f}MB 超过限制 {config.settings.max_file_size / 1024 / 1024}MB"
        return True, None

    # ── 路径解析工具 ─────────────────────────────────────────────────────────

    def _resolve_file_path(self, stored_path: str) -> str:
        """若存储路径在当前环境不存在（如跨平台部署），尝试按 upload_dir 重新解析。"""
        if not stored_path:
            return stored_path
        p = Path(stored_path)
        if p.exists():
            return stored_path
        normalized = stored_path.replace("\\", "/")
        if "uploads/" in normalized:
            parts = normalized.split("uploads/", 1)
            if len(parts) == 2:
                resolved = Path(config.settings.upload_dir) / parts[1]
                if resolved.exists():
                    return str(resolved)
        return stored_path

    # ══════════════════════════════════════════════════════════════════════════
    # conversation 维度公开 API
    # ══════════════════════════════════════════════════════════════════════════

    async def upload_documents(self, conversation_id: Optional[str], files: List[UploadFile]) -> Dict:
        """上传文档到对话。"""
        if conversation_id is None or conversation_id == "new":
            first_filename = files[0].filename if files else "新对话"
            conversation_id = self.conversation_service.create_conversation(title=Path(first_filename).stem if files else None)

        conversation = self.conversation_service.get_conversation(conversation_id)
        if not conversation:
            conversation_id = self.conversation_service.create_conversation(title=None)

        status = self._load_status(conversation_id)
        current_count = len(status.get("documents", {}))
        if current_count + len(files) > config.settings.max_files_per_conversation:
            raise ValueError(
                f"对话已有 {current_count} 个文件，再上传 {len(files)} 个将超过限制 ({config.settings.max_files_per_conversation} 个)"
            )

        uploaded_files = []
        for file in files:
            is_valid, error_msg = self._validate_file(file.filename)
            if not is_valid:
                raise ValueError(error_msg)

            file_content = await file.read()
            is_valid, error_msg = await self._check_file_size(file_content)
            if not is_valid:
                raise ValueError(error_msg)

            file_info = self.file_manager.save_file(
                conversation_id=conversation_id,
                file_content=file_content,
                original_filename=file.filename,
            )
            document_id = file_info["file_id"]
            now = datetime.now(timezone.utc).isoformat()

            document_data = {
                "file_id": document_id,
                "conversation_id": conversation_id,
                "filename": file.filename,
                "file_size": file_info["file_size"],
                "file_extension": file_info["file_extension"],
                "file_path": file_info["file_path"],
                "upload_time": now,
                "status": "pending",
                "lightrag_track_id": None,
            }

            st = self._load_status(conversation_id)
            st.setdefault("documents", {})[document_id] = document_data
            self._save_status(conversation_id, st)
            self.conversation_service.increment_file_count(conversation_id)

            uploaded_files.append({
                "file_id": document_id,
                "filename": file.filename,
                "file_size": file_info["file_size"],
                "status": "pending",
            })

        return {"conversation_id": conversation_id, "uploaded_files": uploaded_files, "total_files": len(uploaded_files)}

    async def process_document(self, conversation_id: str, document_id: str):
        """处理文档（conversation 维度）：解析 → LightRAG 插入（异步后台任务）。"""
        global _processing_queue

        async with _queue_lock:
            _processing_queue.setdefault(conversation_id, [])
            if document_id not in _processing_queue[conversation_id]:
                _processing_queue[conversation_id].append(document_id)

        async with _processing_semaphore:
            doc_info = self.get_document(conversation_id, document_id)
            file_path = doc_info.get("file_path", "") if doc_info else ""

            base_wd = Path(config.settings.lightrag_working_dir)
            base64_file = base_wd.parent / conversation_id / conversation_id / "base_64.json"
            page_index_dir = Path(config.settings.conversations_metadata_dir) / "page_index" / conversation_id

            try:
                await self._process_document_impl(
                    namespace_id=conversation_id,
                    document_id=document_id,
                    file_path=file_path,
                    base64_file=base64_file,
                    page_index_dir=page_index_dir,
                    status_loader=lambda: self._load_status(conversation_id),
                    status_saver=lambda s: self._save_status(conversation_id, s),
                    filename=doc_info.get("filename") if doc_info else None,
                )
            finally:
                async with _queue_lock:
                    if conversation_id in _processing_queue:
                        _processing_queue[conversation_id] = [d for d in _processing_queue[conversation_id] if d != document_id]
                        if not _processing_queue[conversation_id]:
                            del _processing_queue[conversation_id]

    def get_document(self, conversation_id: str, file_id: str) -> Optional[Dict]:
        return self._load_status(conversation_id).get("documents", {}).get(file_id)

    def list_documents(self, conversation_id: str) -> List[Dict]:
        documents = list(self._load_status(conversation_id).get("documents", {}).values())
        documents.sort(key=lambda x: x.get("upload_time", ""), reverse=True)
        return documents

    async def get_document_status(self, conversation_id: str, file_id: str) -> Optional[Dict]:
        document = self.get_document(conversation_id, file_id)
        if not document:
            return None
        status_info = {
            "file_id": file_id,
            "status": document.get("status"),
            "lightrag_track_id": document.get("lightrag_track_id"),
            "error": document.get("error"),
            "upload_time": document.get("upload_time"),
        }
        if document.get("status") == "processing":
            try:
                progress = await self.lightrag_service.get_processing_progress(doc_id=file_id)
                if progress:
                    status_info["progress"] = progress
            except Exception:
                pass
        return status_info

    async def delete_document(self, conversation_id: str, file_id: str) -> bool:
        document = self.get_document(conversation_id, file_id)
        if not document:
            return False

        try:
            # 清理图片缓存
            file_ext = document.get("file_extension", "")
            if file_ext:
                cache_dir = Path(config.settings.image_cache_dir) / file_ext / file_id
                if cache_dir.exists():
                    shutil.rmtree(cache_dir, ignore_errors=True)

            file_deleted = self.file_manager.delete_file(conversation_id, file_id)

            st = self._load_status(conversation_id)
            if file_id in st.get("documents", {}):
                del st["documents"][file_id]
                self._save_status(conversation_id, st)

            self.conversation_service.decrement_file_count(conversation_id)
            return file_deleted
        except Exception as e:
            logger.error("删除文档失败", extra={"event": "doc.delete_error", "file_id": file_id, "error": str(e)})
            return self.file_manager.delete_file(conversation_id, file_id)

    async def _generate_mindmap_async(self, conversation_id: str, document_id: str, document_text: str):
        """异步生成思维脑图（串行处理）。"""
        global _mindmap_semaphore, _mindmap_lock

        conversation = self.conversation_service.get_conversation(conversation_id)
        conversation_title = conversation.get("title", "未命名课程") if conversation else "未命名课程"
        document_info = self.get_document(conversation_id, document_id)
        document_filename = document_info.get("filename", f"文档_{document_id[:8]}") if document_info else f"文档_{document_id[:8]}"

        async with _mindmap_lock:
            if conversation_id not in _mindmap_semaphore:
                _mindmap_semaphore[conversation_id] = asyncio.Semaphore(1)
            semaphore = _mindmap_semaphore[conversation_id]

        async with semaphore:
            try:
                async for _ in self.mindmap_service.generate_mindmap_stream(
                    conversation_id, document_text, conversation_title, document_filename, document_id
                ):
                    pass
            except Exception as e:
                logger.error("思维脑图生成失败", extra={"event": "doc.mindmap_error", "document_id": document_id[:8], "error": str(e)})

    # ══════════════════════════════════════════════════════════════════════════
    # subject 维度公开 API
    # ══════════════════════════════════════════════════════════════════════════

    async def upload_documents_for_subject(self, subject_id: str, files: List[UploadFile]) -> Dict:
        """上传文档到知识库（subject 维度）。"""
        status = self._load_subject_status(subject_id)
        current_count = len(status.get("documents", {}))
        if current_count + len(files) > config.settings.max_files_per_conversation:
            raise ValueError(
                f"知识库已有 {current_count} 个文件，再上传 {len(files)} 个将超过限制 ({config.settings.max_files_per_conversation} 个)"
            )

        uploaded_files = []
        for file in files:
            is_valid, error_msg = self._validate_file(file.filename)
            if not is_valid:
                raise ValueError(error_msg)

            file_content = await file.read()
            is_valid, error_msg = await self._check_file_size(file_content)
            if not is_valid:
                raise ValueError(error_msg)

            file_info = self.file_manager.save_file_for_subject(
                subject_id=subject_id,
                file_content=file_content,
                original_filename=file.filename,
            )
            document_id = file_info["file_id"]
            now = datetime.now(timezone.utc).isoformat()

            document_data = {
                "file_id": document_id,
                "subject_id": subject_id,
                "filename": file.filename,
                "file_size": file_info["file_size"],
                "file_extension": file_info["file_extension"],
                "file_path": file_info["file_path"],
                "upload_time": now,
                "status": "pending",
                "lightrag_track_id": None,
            }

            st = self._load_subject_status(subject_id)
            st.setdefault("documents", {})[document_id] = document_data
            self._save_subject_status(subject_id, st)

            uploaded_files.append({
                "file_id": document_id,
                "filename": file.filename,
                "file_size": file_info["file_size"],
                "status": "pending",
            })

        return {"subject_id": subject_id, "uploaded_files": uploaded_files, "total_files": len(uploaded_files)}

    def list_documents_for_subject(self, subject_id: str) -> List[Dict]:
        documents = list(self._load_subject_status(subject_id).get("documents", {}).values())
        documents.sort(key=lambda x: x.get("upload_time", ""), reverse=True)
        return documents

    def get_document_for_subject(self, subject_id: str, file_id: str) -> Optional[Dict]:
        doc = self._load_subject_status(subject_id).get("documents", {}).get(file_id)
        if not doc:
            return None
        doc = dict(doc)
        if doc.get("file_path"):
            doc["file_path"] = self._resolve_file_path(doc["file_path"])
        return doc

    async def get_document_status_for_subject(self, subject_id: str, file_id: str) -> Optional[Dict]:
        document = self.get_document_for_subject(subject_id, file_id)
        if not document:
            return None
        status_info = {
            "file_id": file_id,
            "status": document.get("status"),
            "lightrag_track_id": document.get("lightrag_track_id"),
            "error": document.get("error"),
            "upload_time": document.get("upload_time"),
        }
        if document.get("status") == "processing":
            try:
                progress = await self.lightrag_service.get_processing_progress(doc_id=file_id)
                if progress:
                    status_info["progress"] = progress
            except Exception:
                pass
        return status_info

    async def delete_document_for_subject(self, subject_id: str, file_id: str) -> bool:
        document = self.get_document_for_subject(subject_id, file_id)
        if not document:
            return False

        try:
            file_ext = document.get("file_extension", "")
            if file_ext:
                cache_dir = Path(config.settings.image_cache_dir) / file_ext / file_id
                if cache_dir.exists():
                    shutil.rmtree(cache_dir, ignore_errors=True)

            file_deleted = self.file_manager.delete_file_for_subject(subject_id, file_id)

            st = self._load_subject_status(subject_id)
            if file_id in st.get("documents", {}):
                del st["documents"][file_id]
                self._save_subject_status(subject_id, st)

            return file_deleted
        except Exception as e:
            logger.error("删除知识库文档失败", extra={"event": "doc.delete_subject_error", "file_id": file_id, "error": str(e)})
            return self.file_manager.delete_file_for_subject(subject_id, file_id)

    async def process_document_for_subject(self, subject_id: str, document_id: str):
        """处理知识库文档（subject 维度）。"""
        document = self.get_document_for_subject(subject_id, document_id)
        if not document:
            logger.error("文档不存在", extra={"event": "doc.not_found", "document_id": document_id})
            return

        file_path = document.get("file_path", "")
        if not file_path or not Path(file_path).exists():
            logger.error("文件不存在", extra={"event": "doc.file_not_found", "file_path": file_path})
            st = self._load_subject_status(subject_id)
            if document_id in st.get("documents", {}):
                st["documents"][document_id]["status"] = "failed"
                st["documents"][document_id]["error"] = "文件不存在"
                self._save_subject_status(subject_id, st)
            return

        base_wd = Path(config.settings.lightrag_working_dir)
        base64_file = base_wd.parent / subject_id / subject_id / "base_64.json"
        page_index_dir = (
            Path(config.settings.conversations_metadata_dir) / "subjects" / subject_id / "page_index"
        )

        async with _processing_semaphore:
            await self._process_document_impl(
                namespace_id=subject_id,
                document_id=document_id,
                file_path=file_path,
                base64_file=base64_file,
                page_index_dir=page_index_dir,
                status_loader=lambda: self._load_subject_status(subject_id),
                status_saver=lambda s: self._save_subject_status(subject_id, s),
                filename=document.get("filename"),
            )

    # ══════════════════════════════════════════════════════════════════════════
    # 向后兼容的页级索引公开方法（供外部调用者使用）
    # ══════════════════════════════════════════════════════════════════════════

    async def build_page_index_json(self, conversation_id: str, document_id: str, file_path: str) -> None:
        doc_info = self.get_document(conversation_id, document_id)
        filename = doc_info.get("filename") if doc_info else None
        index_dir = Path(config.settings.conversations_metadata_dir) / "page_index" / conversation_id
        await self._build_page_index_json_impl(
            conversation_id, document_id, file_path, index_dir, filename=filename
        )

    async def build_page_index_json_for_subject(self, subject_id: str, document_id: str, file_path: str) -> None:
        doc_info = self.get_document_for_subject(subject_id, document_id)
        filename = doc_info.get("filename") if doc_info else None
        index_dir = (
            Path(config.settings.conversations_metadata_dir) / "subjects" / subject_id / "page_index"
        )
        await self._build_page_index_json_impl(
            subject_id, document_id, file_path, index_dir, filename=filename
        )
