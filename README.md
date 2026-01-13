# IndexTTS2 语音合成微服务

> 基于哔哩哔哩 IndexTTS2 模型的零样本语音合成微服务

[![IndexTTS2](https://img.shields.io/badge/IndexTTS2-v2.0-blue)](https://github.com/index-tts/index-tts)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue)](https://www.docker.com)

---

## ✨ 特性

- 🎤 **零样本语音克隆**: 从单个参考音频即可克隆音色
- 😊 **情感控制**: 支持情感语音合成（8 种情感）
- ⚡ **高性能**: 基于 RTX 4090 GPU，1-3 秒/句
- 🔄 **智能缓存**: Redis 缓存相同文本，节省 20-40% 成本
- 📊 **按需启停**: 空闲自动关机，节省 70-85% 成本
- 🐳 **容器化**: Docker 一键部署

---

## 🚀 快速开始

### 方式 1: Docker Compose（本地开发）

```bash
# 克隆仓库
git clone https://github.com/your-org/indextts2-service.git
cd indextts2-service

# 配置环境变量
cp .env.example .env

# 启动服务（需要 GPU 支持）
docker-compose up --build

# 访问 API 文档
open http://localhost:8000/docs
```

### 方式 2: RunPod 部署（生产环境）

#### 步骤 1: 构建 Docker 镜像

```bash
docker build -t your-registry/indextts2-service:latest .
docker push your-registry/indextts2-service:latest
```

#### 步骤 2: 创建 RunPod 模板

1. 登录 [RunPod Console](https://www.runpod.io/console)
2. 创建 -> Custom Docker Image
3. 配置:
   - **镜像**: `your-registry/indextts2-service:latest`
   - **GPU**: RTX 4090
   - **容器磁盘**: 50GB
   - **端口**: 8000
   - **环境变量**:
     ```
     MODEL_DIR=/app/checkpoints
     USE_FP16=true
     ```

#### 步骤 3: 启动实例

```bash
# 使用 RunPod API
curl -X POST https://api.runpod.io/v2/$TEMPLATE_ID/pods \
  -H "Authorization: Bearer $RUNPOD_API_KEY" \
  -d '{
    "name": "indextts2-service",
    "gpuCount": 1
  }'
```

---

## 📖 API 使用

### 语音克隆

```bash
curl -X POST "https://your-service.com/api/tts/clone" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "很久很久以前，在一片神奇的森林里...",
    "audio_prompt_url": "https://example.com/voice_sample.wav"
  }'
```

**响应**:

```json
{
  "audio_url": "https://s3.amazonaws.com/bucket/tts_abc123.wav",
  "duration": 5.23,
  "text": "很久很久以前，在一片神奇的森林里...",
  "sample_rate": 48000
}
```

### 带情感的语音合成

```bash
curl -X POST "https://your-service.com/api/tts/clone" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "今天天气真好！",
    "audio_prompt_url": "https://example.com/voice.wav",
    "emotion_url": "https://example.com/happy_emotion.wav",
    "emotion_alpha": 0.8
  }'
```

---

## 💰 成本分析

| 场景 | 日运行 | 月成本 | 年成本 |
|------|--------|--------|--------|
| 最低 | 2h | $20-26 | $240-312 |
| 中等 | 6h | $61-89 | $732-1,068 |
| 最高 | 12h | $122-158 | $1,464-1,896 |

**对比 ElevenLabs**: 节省 60-80%

详细分析见: [gpu-cost-analysis-2026.md](https://github.com/your-org/MagicTale/docs/gpu-cost-analysis-2026.md)

---

## 🔧 配置说明

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `MODEL_DIR` | 模型文件目录 | `./checkpoints` |
| `USE_FP16` | FP16 推理 | `true` |
| `S3_BUCKET` | S3 存储桶 | - |
| `REDIS_URL` | Redis 连接 | - |
| `RUNPOD_API_KEY` | RunPod API Key | - |

### 模型下载

首次运行需要下载 IndexTTS2 模型（~2GB）:

```bash
# 方式 1: 使用 Hugging Face CLI
pip install "huggingface-hub[cli]"
hf download IndexTeam/IndexTTS-2 --local-dir checkpoints

# 方式 2: 使用 ModelScope（国内）
pip install modelscope
modelscope download --model IndexTeam/IndexTTS-2 --local_dir checkpoints
```

---

## 📁 项目结构

```
indextts2-service/
├── app/                    # 应用代码
│   ├── main.py            # FastAPI 入口
│   ├── api/               # API 路由
│   │   └── tts.py         # TTS 接口
│   └── services/          # 业务逻辑
│       └── indextts.py    # IndexTTS2 封装
├── checkpoints/           # 模型文件（~2GB）
├── tests/                # 测试
├── scripts/              # 工具脚本
├── Dockerfile            # Docker 镜像
├── docker-compose.yml    # 本地开发
├── pyproject.toml       # Python 依赖
└── README.md
```

---

## 🔗 相关链接

- [IndexTTS2 GitHub](https://github.com/index-tts/index-tts)
- [IndexTTS2 论文](https://arxiv.org/abs/2506.21619)
- [RunPod 官网](https://www.runpod.io/)
- [技术方案文档](https://github.com/your-org/MagicTale/docs/indextts2-technical-solution.md)

---

## 📄 许可证

MIT License

---

*最后更新: 2026-01-13*
