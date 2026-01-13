#!/bin/bash
# RunPod 部署脚本

set -e

# 配置
IMAGE_NAME="${1:-indextts2-service}"
IMAGE_TAG="${2:-latest}"
REGISTRY="${REGISTRY:-docker.io/your-org}"

FULL_IMAGE="$REGISTRY/$IMAGE_NAME:$IMAGE_TAG"

echo "======================================="
echo "IndexTTS2 微服务部署脚本"
echo "======================================="
echo "镜像: $FULL_IMAGE"
echo ""

# 1. 构建镜像
echo "📦 构建 Docker 镜像..."
docker build -t "$FULL_IMAGE" .
echo "✅ 镜像构建完成"
echo ""

# 2. 登录镜像仓库
echo "🔐 登录镜像仓库..."
docker login "$REGISTRY"
echo "✅ 登录成功"
echo ""

# 3. 推送镜像
echo "⬆️  推送镜像到仓库..."
docker push "$FULL_IMAGE"
echo "✅ 镜像推送完成"
echo ""

# 4. 检查 RunPod API Key
if [ -z "$RUNPOD_API_KEY" ]; then
    echo "⚠️  未设置 RUNPOD_API_KEY 环境变量"
    echo "请先设置: export RUNPOD_API_KEY=your_key"
    exit 1
fi

# 5. 创建 RunPod 模板（如果不存在）
TEMPLATE_ID="${RUNPOD_TEMPLATE_ID:-}"

if [ -z "$TEMPLATE_ID" ]; then
    echo "📝 创建 RunPod 模板..."
    echo "请在 RunPod Console 手动创建模板，或提供 TEMPLATE_ID"
    echo ""
    echo "模板配置:"
    echo "  - 镜像: $FULL_IMAGE"
    echo "  - GPU: RTX 4090"
    echo "  - 容器磁盘: 50GB"
    echo "  - 端口: 8000"
    echo ""
    echo "创建后请设置环境变量:"
    echo "  export RUNPOD_TEMPLATE_ID=template-xxx"
    exit 0
fi

# 6. 启动 Pod
echo "🚀 启动 GPU 实例..."
RESPONSE=$(curl -s -X POST "https://api.runpod.io/v2/$TEMPLATE_ID/pods" \
  -H "Authorization: Bearer $RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"indextts2-service\",
    \"gpuCount\": 1
  }")

POD_ID=$(echo "$RESPONSE" | jq -r '.id')

if [ "$POD_ID" != "null" ] && [ -n "$POD_ID" ]; then
    echo "✅ Pod 启动成功: $POD_ID"
    echo ""
    echo "等待实例就绪..."

    # 等待 Pod 启动
    sleep 30

    # 获取 Pod 状态
    curl -s "https://api.runpod.io/v2/pods/$POD_ID" \
      -H "Authorization: Bearer $RUNPOD_API_KEY" \
      -H "Content-Type: application/json" | jq '.'

    echo ""
    echo "🎉 部署完成！"
    echo ""
    echo "查看日志: docker logs -f indextts2-service"
    echo "停止实例: ./scripts/stop-runpod.sh $POD_ID"
else
    echo "❌ Pod 启动失败"
    echo "$RESPONSE"
    exit 1
fi
