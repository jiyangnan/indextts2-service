"""
IndexTTS2 语音合成微服务

FastAPI 应用入口
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import tts
import logging

logger = logging.getLogger(__name__)

app = FastAPI(
    title="IndexTTS2 Service",
    description="零样本语音合成微服务 - 基于哔哩哔哩 IndexTTS2 模型",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境需限制
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(tts.router, prefix="/api", tags=["tts"])

# 启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动时初始化"""
    logger.info("Starting IndexTTS2 Service...")

    # 预加载模型
    from app.services.indextts import indextts_service
    await indextts_service.warmup()

    logger.info("IndexTTS2 Service started successfully")

# 关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理"""
    logger.info("Shutting down IndexTTS2 Service...")

# 健康检查
@app.get("/health")
async def health_check():
    """
    健康检查端点
    """
    from app.services.indextts import indextts_service

    return {
        "status": "healthy",
        "service": "indextts2",
        "version": "2.0.0",
        "model_loaded": indextts_service.is_loaded(),
        "gpu_available": indextts_service.gpu_available()
    }

# 根路径
@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "IndexTTS2",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    import uvicorn
    import os
    from dotenv import load_dotenv

    # 加载环境变量
    load_dotenv()

    uvicorn.run(
        "app.main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", "8001")),
        reload=True,
        log_level=os.getenv("LOG_LEVEL", "info")
    )
