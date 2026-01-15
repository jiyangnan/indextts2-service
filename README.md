# IndexTTS2 语音合成微服务

> 基于哔哩哔哩 IndexTTS2 模型的零样本语音合成微服务

[![IndexTTS2](https://img.shields.io/badge/IndexTTS2-v2.0-blue)](https://github.com/index-tts/index-tts)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue)](https://www.docker.com)

---

## ✨ 特性

- 🎤 **零样本语音克隆**: 从单个参考音频即可克隆音色
- 😊 **情感控制**: 支持情感语音合成（8 种情感）
- ⚡ **高性能**: 基于 RTX 3070 GPU，1-3 秒/句
- 🔄 **智能缓存**: Redis 缓存相同文本，节省 20-40% 成本
- 📊 **按需启停**: 空闲自动关机，节省 70-85% 成本
- 💰 **超低成本**: 仅 $0.07/小时，月成本约 $12.6（6h/天）
- 🐳 **容器化**: Docker 一键部署 + GHCR 镜像仓库

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
open http://localhost:8001/docs
```

### 方式 2: RunPod 部署（生产环境）⭐

**GPU 选型**: RTX 3070 (@ $0.07/小时) - 月成本约 $12.6（6h/天）

#### 步骤 1: 准备 GitHub Personal Access Token

1. 访问: https://github.com/settings/tokens
2. 生成新的 Token（需要 `write:packages` 权限）
3. 设置环境变量:
   ```bash
   export GITHUB_PAT=your_token_here
   ```

#### 步骤 2: 使用部署脚本（推荐）

```bash
# 克隆仓库
git clone https://github.com/jiyangnan/indextts2-service.git
cd indextts2-service

# 设置环境变量
export RUNPOD_API_KEY=rpa_xxx...
export RUNPOD_TEMPLATE_ID=template-xxx  # 从步骤 3 获取

# 一键部署（构建、推送、启动）
make docker-push
```

#### 步骤 3: 创建 RunPod 模板

1. 登录 [RunPod Console](https://www.runpod.io/console)
2. 导航到: **Templates** → **Create Template**
3. 配置模板:
   - **Name**: `indextts2-service`
   - **Docker Image**: `ghcr.io/jiyangnan/indextts2-service:latest`
   - **GPU Type**: `NVIDIA RTX 3070` ⭐ **$0.07/小时**
   - **Container Disk**: `50GB`
   - **Volume Disk**: `20GB` (用于缓存)
   - **Ports**: `8001` (HTTP)
   - **Env Vars**:
     ```env
     MODEL_DIR=/app/checkpoints
     USE_FP16=true
     API_PORT=8001
     SUPABASE_URL=https://your-supabase-url.supabase.co
     SUPABASE_SERVICE_KEY=your_service_key
     SUPABASE_STORAGE_BUCKET=magictale
     ```
4. 保存模板，记录 **Template ID**

#### 步骤 4: 启动实例

```bash
# 设置环境变量
export RUNPOD_API_KEY=rpa_xxx...
export RUNPOD_TEMPLATE_ID=template-xxx

# 启动实例
./scripts/start-runpod.sh
```

**脚本会自动**:
1. 启动 GPU 实例
2. 等待实例就绪
3. 显示实例 IP 和端口
4. 测试健康检查

#### 手动启动（可选）

```bash
# 使用 RunPod API
curl -X POST https://api.runpod.io/v2/$TEMPLATE_ID/pods \
  -H "Authorization: Bearer $RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "indextts2-service",
    "gpuCount": 1,
    "minMinutes": 10
  }'
```

#### 停止实例

```bash
# 使用脚本
./scripts/stop-runpod.sh <pod_id>

# 或使用 API
curl -X POST https://api.runpod.io/v2/pods/<pod_id>/terminate \
  -H "Authorization: Bearer $RUNPOD_API_KEY"
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

### GPU 选型对比

| GPU 型号 | 价格/小时 | 月成本（6h/天） | 显存 | 性价比 |
|---------|----------|----------------|------|--------|
| **RTX 3070** ⭐ | **$0.07** | **~$12.6** | 8GB | 🏆 最高 |
| RTX 3080 | $0.09 | ~$16.2 | 10GB | ✅ 良好 |
| RTX A4000 | $0.09 | ~$16.2 | 16GB | ✅ 良好 |
| ~~RTX 4090~~ | ~~$0.34~~ | ~~$61.2~~ | 24GB | ❌ 太贵 |

**推荐**: RTX 3070（实测 128MB 显卡即可运行，8GB 绰绰有余）

### 使用场景成本

| 场景 | 日运行 | 月成本 (RTX 3070) | 年成本 |
|------|--------|------------------|--------|
| 最低 | 2h | **$4.2** | **$50.4** |
| 中等 | 6h | **$12.6** | **$151.2** |
| 最高 | 12h | **$25.2** | **$302.4** |

**对比 ElevenLabs**: 节省 85-90%

**自动启停节省**: 空闲 10 分钟自动停止，额外节省 70-85%

详细分析见: [gpu-cost-analysis-2026.md](https://github.com/your-org/MagicTale/docs/gpu-cost-analysis-2026.md)

---

## 🔧 配置说明

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `MODEL_DIR` | 模型文件目录 | `./checkpoints` |
| `USE_FP16` | FP16 推理 | `true` |
| `API_PORT` | API 端口 | `8001` |
| `SUPABASE_URL` | Supabase URL | - |
| `SUPABASE_SERVICE_KEY` | Supabase Service Key | - |
| `SUPABASE_STORAGE_BUCKET` | 存储桶名称 | `magictale` |
| `REDIS_URL` | Redis 连接 | - |
| `RUNPOD_API_KEY` | RunPod API Key | - |
| `RUNPOD_TEMPLATE_ID` | RunPod 模板 ID | - |
| `IDLE_TIMEOUT_MINUTES` | 空闲超时（分钟） | `10` |

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
- [RunPod GPU 定价](https://www.runpod.io/gpu-pricing)
- [技术方案文档](https://github.com/jiyangnan/MagicTale/docs/indextts2-technical-solution.md)

---

## 📄 许可证

MIT License

---

*最后更新: 2026-01-15*
