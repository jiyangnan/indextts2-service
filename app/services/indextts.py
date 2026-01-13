"""
IndexTTS2 服务封装

提供 IndexTTS2 模型的加载、推理和管理功能
"""

import asyncio
import logging
import os
import tempfile
import urllib.request
from pathlib import Path
from typing import Optional, Tuple

import torch

logger = logging.getLogger(__name__)

# IndexTTS2 模型路径
MODEL_DIR = os.getenv("MODEL_DIR", "./checkpoints")
CONFIG_PATH = os.getenv("CONFIG_PATH", os.path.join(MODEL_DIR, "config.yaml"))


class IndexTTS2Service:
    """
    IndexTTS2 服务封装

    特性:
    - 单例模式，避免重复加载模型
    - 懒加载，首次使用时才加载
    - 线程安全的模型访问
    - GPU 可用性检测
    """

    _instance: Optional['IndexTTS2Service'] = None
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self._model = None
        self._device = None
        self._loaded = False

    async def get_model(self):
        """
        获取 IndexTTS2 模型实例（懒加载）

        Returns:
            IndexTTS2 模型实例
        """
        if self._model is None:
            async with self._lock:
                # 双重检查
                if self._model is None:
                    logger.info("Loading IndexTTS2 model...")
                    await self._load_model()
                    logger.info("IndexTTS2 model loaded successfully")
        return self._model

    async def _load_model(self):
        """
        加载 IndexTTS2 模型

        在线程池中执行，避免阻塞事件循环
        """
        loop = asyncio.get_event_loop()

        def _load():
            # 检查 CUDA 可用性
            if torch.cuda.is_available():
                device = torch.device("cuda")
                logger.info(f"CUDA available: {torch.cuda.get_device_name(0)}")
            else:
                device = torch.device("cpu")
                logger.warning("CUDA not available, using CPU")

            # 动态导入 IndexTTS2
            try:
                from indextts.infer_v2 import IndexTTS2 as TTSModel
            except ImportError:
                # 如果未安装，使用模拟实现
                logger.warning("IndexTTS2 not installed, using mock implementation")
                TTSModel = self._create_mock_model()

            # 初始化模型
            model = TTSModel(
                cfg_path=CONFIG_PATH,
                model_dir=MODEL_DIR,
                use_fp16=os.getenv("USE_FP16", "true").lower() == "true",
                use_cuda_kernel=os.getenv("USE_CUDA_KERNEL", "false").lower() == "true",
                use_deepspeed=os.getenv("USE_DEEPSPEED", "false").lower() == "true"
            )

            self._model = model
            self._device = device
            self._loaded = True

            return model

        # 在线程池中执行（避免阻塞）
        await loop.run_in_executor(None, _load)

    async def warmup(self):
        """
        预热模型

        执行一次推理以初始化模型状态
        """
        try:
            logger.info("Warming up IndexTTS2 model...")
            model = await self.get_model()

            # 执行一次推理（使用空文本或极短文本）
            if hasattr(model, 'infer'):
                # 真实模型
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as f:
                    # 下载或创建临时音频文件
                    temp_audio = await self._create_temp_audio()
                    await self._run_inference(
                        model=model,
                        text="Hello",
                        audio_prompt_path=temp_audio,
                        output_path=f.name
                    )
            else:
                # Mock 模型
                pass

            logger.info("Model warmup completed")

        except Exception as e:
            logger.error(f"Model warmup failed: {e}")
            # 预热失败不阻止服务启动

    async def synthesize(
        self,
        text: str,
        audio_prompt_url: str,
        emotion_url: Optional[str] = None,
        emotion_alpha: float = 1.0,
        output_path: Optional[str] = None
    ) -> Tuple[bytes, float]:
        """
        语音合成

        Args:
            text: 要合成的文本
            audio_prompt_url: 参考音频 URL
            emotion_url: 情感音频 URL（可选）
            emotion_alpha: 情感强度 0.0-1.0
            output_path: 输出文件路径（可选）

        Returns:
            (audio_bytes, duration_seconds)
        """
        model = await self.get_model()

        # 下载音频参考
        audio_prompt_path = await self._download_audio(audio_prompt_url)

        # 下载情感音频（如果有）
        emotion_path = None
        if emotion_url:
            emotion_path = await self._download_audio(emotion_url)

        # 生成输出路径
        if not output_path:
            import uuid
            output_path = f"/tmp/tts_{uuid.uuid4().hex}.wav"

        # 执行推理
        await self._run_inference(
            model=model,
            text=text,
            audio_prompt_path=audio_prompt_path,
            emotion_path=emotion_path,
            emotion_alpha=emotion_alpha,
            output_path=output_path
        )

        # 读取生成的音频
        with open(output_path, "rb") as f:
            audio_bytes = f.read()

        # 获取音频时长
        duration = self._get_audio_duration(output_path)

        # 清理临时文件
        try:
            os.remove(audio_prompt_path)
            if emotion_path:
                os.remove(emotion_path)
        except:
            pass

        return audio_bytes, duration

    async def _run_inference(
        self,
        model,
        text: str,
        audio_prompt_path: str,
        output_path: str,
        emotion_path: Optional[str] = None,
        emotion_alpha: float = 1.0
    ):
        """
        执行推理（在线程池中）
        """
        loop = asyncio.get_event_loop()

        def _infer():
            kwargs = {
                "spk_audio_prompt": audio_prompt_path,
                "text": text,
                "output_path": output_path,
                "verbose": False
            }

            # 添加情感参数（如果有）
            if emotion_path:
                kwargs["emo_audio_prompt"] = emotion_path
                kwargs["emo_alpha"] = emotion_alpha

            # 调用模型推理
            if hasattr(model, 'infer'):
                model.infer(**kwargs)
            else:
                # Mock 实现
                self._mock_inference(**kwargs)

        await loop.run_in_executor(None, _infer)

    async def _download_audio(self, url: str) -> str:
        """
        下载音频文件到临时目录

        Args:
            url: 音频 URL

        Returns:
            本地文件路径
        """
        import uuid

        temp_path = f"/tmp/audio_{uuid.uuid4().hex}.wav"

        # 下载文件
        try:
            urllib.request.urlretrieve(url, temp_path)
        except Exception as e:
            logger.error(f"Failed to download audio from {url}: {e}")
            # 创建空文件（fallback）
            Path(temp_path).touch()

        return temp_path

    async def _create_temp_audio(self) -> str:
        """创建临时音频文件（用于预热）"""
        import wave
        import uuid

        temp_path = f"/tmp/warmup_{uuid.uuid4().hex}.wav"

        # 创建一个 1 秒的静音 WAV
        with wave.open(temp_path, 'w') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(48000)
            wav.writeframes(b'\x00' * 96000)  # 1 秒静音

        return temp_path

    def _get_audio_duration(self, audio_path: str) -> float:
        """获取音频时长"""
        try:
            import wave
            with wave.open(audio_path, 'rb') as wav:
                frames = wav.getnframes()
                rate = wav.getframerate()
                return frames / rate
        except:
            # Fallback: 使用文件大小估算
            return len(open(audio_path, 'rb').read()) / 96000

    def is_loaded(self) -> bool:
        """检查模型是否已加载"""
        return self._loaded and self._model is not None

    def gpu_available(self) -> bool:
        """检查 GPU 是否可用"""
        return torch.cuda.is_available()

    def _create_mock_model(self):
        """创建 Mock 模型（用于开发测试）"""
        class MockIndexTTS2:
            def __init__(self, **kwargs):
                pass

            def infer(self, **kwargs):
                output_path = kwargs.get('output_path', '/tmp/mock.wav')
                # 创建一个空的 WAV 文件
                import wave
                with wave.open(output_path, 'w') as wav:
                    wav.setnchannels(1)
                    wav.setsampwidth(2)
                    wav.setframerate(48000)
                    # 写入 1 秒静音
                    wav.writeframes(b'\x00' * 96000)

        return MockIndexTTS2

    def _mock_inference(self, **kwargs):
        """Mock 推理实现"""
        output_path = kwargs.get('output_path', '/tmp/mock.wav')
        import wave

        # 根据 text 长度估算时长
        text = kwargs.get('text', '')
        duration = max(1, len(text) * 0.15)  # 约 0.15 秒/字符

        with wave.open(output_path, 'w') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(48000)
            frames = int(48000 * duration)
            wav.writeframes(b'\x00' * frames)


# 单例实例
indextts_service = IndexTTS2Service()
