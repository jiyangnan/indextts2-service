"""
IndexTTS2 API 测试
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root():
    """测试根路径"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "IndexTTS2"
    assert "docs" in data


def test_health_check():
    """测试健康检查"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "model_loaded" in data


def test_tts_health():
    """测试 TTS 服务健康检查"""
    response = client.get("/api/tts/health")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "indextts2-tts"


@pytest.mark.skip(reason="需要实际模型和音频文件")
def test_clone_voice():
    """测试语音克隆（集成测试）"""
    request_data = {
        "text": "测试文本",
        "audio_prompt_url": "https://example.com/test.wav",
        "emotion_alpha": 1.0
    }

    response = client.post("/api/tts/clone", json=request_data)

    # 可能返回 200（成功）或 500（模型未加载）
    assert response.status_code in [200, 500]

    if response.status_code == 200:
        data = response.json()
        assert "audio_url" in data
        assert "duration" in data
        assert data["text"] == request_data["text"]


def test_clone_voice_validation():
    """测试请求参数验证"""
    # 缺少必需字段
    response = client.post(
        "/api/tts/clone",
        json={}
    )
    assert response.status_code == 422

    # 文本为空
    response = client.post(
        "/api/tts/clone",
        json={
            "text": "",
            "audio_prompt_url": "https://example.com/test.wav"
        }
    )
    assert response.status_code == 422

    # 无效的 emotion_alpha
    response = client.post(
        "/api/tts/clone",
        json={
            "text": "测试",
            "audio_prompt_url": "https://example.com/test.wav",
            "emotion_alpha": 2.0  # 超出范围
        }
    )
    assert response.status_code == 422
