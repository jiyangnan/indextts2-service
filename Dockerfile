# IndexTTS2 微服务 Dockerfile
# 多阶段构建，优化镜像大小

# 阶段 1: 基础镜像
FROM nvidia/cuda:12.8.0-runtime-ubuntu22.04 AS base

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    python3-dev \
    git \
    git-lfs \
    ffmpeg \
    libsndfile1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装 git-lfs
RUN git lfs install

# 设置工作目录
WORKDIR /app

# 阶段 2: 依赖安装
FROM base AS dependencies

# 安装 uv (新一代 Python 包管理器)
COPY pyproject.toml ./
RUN pip install --no-cache-dir uv

# 安装项目依赖
RUN uv sync --all-extras

# 阶段 3: 模型下载
FROM base AS model-download

# 安装 Hugging Face CLI
RUN pip install --no-cache-dir "huggingface-hub[cli]"

# 下载 IndexTTS2 模型
# 注意: 首次运行会下载约 2GB 的模型文件
RUN hf download IndexTeam/IndexTTS-2 --local-dir /tmp/checkpoints

# 阶段 4: 最终镜像
FROM base AS final

# 安装 Python 依赖
COPY pyproject.toml ./
RUN pip install --no-cache-dir uv
RUN uv sync --all-extras --no-dev

# 复制应用代码
COPY app ./app

# 从 model-download 阶段复制模型
COPY --from=model-download /tmp/checkpoints ./checkpoints

# 创建必要的目录
RUN mkdir -p /tmp /data/audio

# 环境变量
ENV PYTHONPATH=/app
ENV MODEL_DIR=/app/checkpoints
ENV CONFIG_PATH=/app/checkpoints/config.yaml
ENV USE_FP16=true
ENV USE_CUDA_KERNEL=false
ENV USE_DEEPSPEED=false

# 暴露端口（8001 避免与 MagicTale 后端 8000 冲突）
EXPOSE 8001

# 环境变量（添加 API_PORT）
ENV API_PORT=8001

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# 启动命令
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
