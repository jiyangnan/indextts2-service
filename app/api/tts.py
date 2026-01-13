"""
TTS API 路由

提供语音合成相关的 HTTP 接口
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, validator
from typing import Optional
import logging
import uuid
import os

from app.services.indextts import indextts_service

logger = logging.getLogger(__name__)
router = APIRouter()


class TTSRequest(BaseModel):
    """语音合成请求模型"""

    text: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="要合成的文本（1-5000 字符）"
    )
    audio_prompt_url: str = Field(
        ...,
        description="参考音频 URL（用于克隆音色）"
    )
    emotion_url: Optional[str] = Field(
        None,
        description="情感音频 URL（可选，用于情感控制）"
    )
    emotion_alpha: float = Field(
        1.0,
        ge=0.0,
        le=1.0,
        description="情感强度 0.0-1.0（默认 1.0）"
    )

    @validator('text')
    def validate_text(cls, v):
        """验证文本不为空"""
        if not v or not v.strip():
            raise ValueError('text 不能为空')
        return v.strip()

    @validator('audio_prompt_url')
    def validate_audio_url(cls, v):
        """验证音频 URL"""
        if not v or not v.startswith(('http://', 'https://')):
            raise ValueError('audio_prompt_url 必须是有效的 URL')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "text": "很久很久以前，在一片神奇的森林里，住着一只可爱的小兔子。",
                "audio_prompt_url": "https://example.com/voice_sample.wav",
                "emotion_url": None,
                "emotion_alpha": 1.0
            }
        }


class TTSResponse(BaseModel):
    """语音合成响应模型"""

    audio_url: str = Field(..., description="生成的音频 URL")
    duration: float = Field(..., description="音频时长（秒）")
    text: str = Field(..., description="合成的文本")
    sample_rate: int = Field(default=48000, description="采样率")

    class Config:
        json_schema_extra = {
            "example": {
                "audio_url": "https://s3.amazonaws.com/bucket/tts_abc123.wav",
                "duration": 5.23,
                "text": "很久很久以前，在一片神奇的森林里，住着一只可爱的小兔子。",
                "sample_rate": 48000
            }
        }


@router.post(
    "/tts/clone",
    response_model=TTSResponse,
    status_code=status.HTTP_200_OK,
    summary="零样本语音克隆",
    description="使用参考音频克隆音色，并合成指定文本的语音"
)
async def clone_voice(request: TTSRequest) -> TTSResponse:
    """
    零样本语音克隆 + 文本转语音

    ## 功能说明

    1. **音色克隆**: 从 `audio_prompt_url` 提取音色特征
    2. **情感控制** (可选): 从 `emotion_url` 提取情感特征
    3. **语音合成**: 使用 IndexTTS2 模型生成语音

    ## 参数说明

    - **text**: 要合成的文本（1-5000 字符）
    - **audio_prompt_url**: 参考音频 URL（用于克隆音色）
    - **emotion_url**: 情感音频 URL（可选）
    - **emotion_alpha**: 情感强度 0.0-1.0，默认 1.0

    ## 返回

    - **audio_url**: 生成的音频 URL（上传到对象存储）
    - **duration**: 音频时长（秒）
    - **text**: 合成的文本
    - **sample_rate**: 采样率（默认 48000 Hz）

    ## 示例

    ```bash
    curl -X POST "https://your-service.com/api/tts/clone" \
      -H "Content-Type: application/json" \
      -d '{
        "text": "很久很久以前，在一片神奇的森林里...",
        "audio_prompt_url": "https://example.com/voice.wav"
      }'
    ```
    """
    try:
        logger.info(f"TTS request: text_length={len(request.text)}, "
                   f"audio_prompt={request.audio_prompt_url[:50]}...")

        # 调用 IndexTTS2 服务
        audio_bytes, audio_duration = await indextts_service.synthesize(
            text=request.text,
            audio_prompt_url=request.audio_prompt_url,
            emotion_url=request.emotion_url,
            emotion_alpha=request.emotion_alpha
        )

        # 上传到对象存储
        audio_url = await _upload_to_storage(
            audio_bytes=audio_bytes,
            filename=f"tts_{uuid.uuid4().hex}.wav"
        )

        logger.info(f"TTS completed: duration={audio_duration:.2f}s, url={audio_url}")

        return TTSResponse(
            audio_url=audio_url,
            duration=audio_duration,
            text=request.text,
            sample_rate=48000
        )

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.exception(f"TTS generation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"语音合成失败: {str(e)}"
        )


async def _upload_to_storage(audio_bytes: bytes, filename: str) -> str:
    """
    上传音频到对象存储

    支持:
    - AWS S3
    - 阿里云 OSS
    - 本地存储（开发环境）
    """
    import boto3
    from urllib.parse import urljoin

    # 优先级: S3 > OSS > 本地
    s3_endpoint = os.getenv("S3_ENDPOINT")
    s3_bucket = os.getenv("S3_BUCKET")
    s3_access_key = os.getenv("S3_ACCESS_KEY_ID")
    s3_secret_key = os.getenv("S3_SECRET_ACCESS_KEY")

    # AWS S3 / 兼容 S3
    if s3_bucket and s3_access_key and s3_secret_key:
        s3_client = boto3.client(
            's3',
            endpoint_url=s3_endpoint,
            aws_access_key_id=s3_access_key,
            aws_secret_access_key=s3_secret_key
        )

        key = f"tts/{filename}"
        s3_client.put_object(
            Bucket=s3_bucket,
            Key=key,
            Body=audio_bytes,
            ContentType='audio/wav'
        )

        # 返回公开 URL
        if s3_endpoint:
            # 自定义 S3 兼容存储
            base_url = s3_endpoint.rstrip('/')
            return urljoin(base_url, f"{s3_bucket}/{key}")
        else:
            # AWS S3
            return f"https://{s3_bucket}.s3.amazonaws.com/{key}"

    # 阿里云 OSS
    oss_endpoint = os.getenv("OSS_ENDPOINT")
    oss_bucket = os.getenv("OSS_BUCKET")
    oss_key = os.getenv("OSS_ACCESS_KEY_ID")
    oss_secret = os.getenv("OSS_SECRET_ACCESS_KEY")

    if oss_endpoint and oss_bucket and oss_key and oss_secret:
        # 这里可以集成 oss2 库
        pass

    # 本地存储（开发环境）
    local_dir = os.getenv("LOCAL_STORAGE_DIR", "./data/audio")
    os.makedirs(local_dir, exist_ok=True)

    local_path = os.path.join(local_dir, filename)
    with open(local_path, "wb") as f:
        f.write(audio_bytes)

    # 返回本地文件 URL（开发环境）
    base_url = os.getenv("LOCAL_BASE_URL", "http://localhost:8000")
    return urljoin(base_url, f"audio/{filename}")


@router.get(
    "/tts/health",
    summary="服务健康检查",
    description="检查 TTS 服务和模型状态"
)
async def tts_health_check():
    """TTS 服务健康检查"""
    return {
        "service": "indextts2-tts",
        "status": "healthy",
        "model_loaded": indextts_service.is_loaded(),
        "gpu_available": indextts_service.gpu_available()
    }
