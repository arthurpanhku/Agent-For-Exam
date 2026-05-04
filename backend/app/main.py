from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.config import settings
from app.api import conversations, documents, graph, images, mindmap_routes, subjects, studyforge_ai
from app.api import settings as settings_api
from app.api import subject_documents
from app.api import exams
from app.services.config_service import config_service
from app.middleware.http import APIKeyMiddleware, RequestIDMiddleware
from app.openapi import build_custom_openapi
from app.exception_handlers import http_exception_handler, unhandled_exception_handler

app = FastAPI(
    title="StudyForge API",
    description="StudyForge — structured retrieval and study workspace API.",
    version="1.0.0"
)

app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)
app.openapi = build_custom_openapi(app)

# 配置日志
import logging
import sys

# 强制配置基础日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
    force=True  # 强制覆盖 Uvicorn 的默认配置
)

# 确保 app 命名空间的日志级别为 INFO
logging.getLogger("app").setLevel(logging.INFO)

# CORS 配置（最先注册的在 Starlette 栈中最靠近路由）
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key", "X-Request-ID"],
    expose_headers=["X-Request-ID"],
)

# 可选 API Key（内侧）；最外层为请求 ID，便于拒绝请求也带上关联 ID
app.add_middleware(APIKeyMiddleware)
app.add_middleware(RequestIDMiddleware)

# 挂载静态文件服务（用于访问上传的图片）
data_dir = Path(settings.data_dir)
if data_dir.exists():
    app.mount("/uploads", StaticFiles(directory=str(data_dir)), name="uploads")
    # 🆕 添加 /data 路由，方便前端访问图片
    app.mount("/data", StaticFiles(directory=str(data_dir)), name="data")

# 注册路由
app.include_router(conversations.router)
app.include_router(subjects.router)
app.include_router(documents.router)
app.include_router(subject_documents.router)
app.include_router(graph.router)
app.include_router(images.router)
app.include_router(mindmap_routes.router)
app.include_router(settings_api.router)
app.include_router(exams.router)
app.include_router(studyforge_ai.router)

# 启动时加载配置
@app.on_event("startup")
async def startup_event():
    """启动时加载配置并尝试同步模型列表"""
    config_service.reload_all_configs()
    await config_service.startup_refresh_models()

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "StudyForge API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}
