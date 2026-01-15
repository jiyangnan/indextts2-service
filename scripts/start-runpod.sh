#!/bin/bash
# RunPod 启动脚本 - 启动 IndexTTS2 微服务实例

set -e

# 配置
TEMPLATE_ID="${RUNPOD_TEMPLATE_ID:-}"
POD_NAME="${POD_NAME:-indextts2-service}"
GPU_COUNT="${GPU_COUNT:-1}"
MINUTES="${IDLE_TIMEOUT_MINUTES:-10}"

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "======================================="
echo "🚀 RunPod 启动脚本"
echo "======================================="
echo "模板 ID: ${TEMPLATE_ID:-(未设置)}"
echo "Pod 名称: $POD_NAME"
echo "GPU 数量: $GPU_COUNT"
echo "空闲超时: $MINUTES 分钟"
echo ""

# 检查 RunPod API Key
if [ -z "$RUNPOD_API_KEY" ]; then
    echo -e "${RED}❌ 未设置 RUNPOD_API_KEY 环境变量${NC}"
    echo "请先设置: export RUNPOD_API_KEY=your_key"
    exit 1
fi

# 检查 Template ID
if [ -z "$TEMPLATE_ID" ]; then
    echo -e "${RED}❌ 未设置 RUNPOD_TEMPLATE_ID 环境变量${NC}"
    echo ""
    echo "请先在 RunPod Console 创建模板："
    echo "  1. 登录 https://www.runpod.io/console"
    echo "  2. 导航到 Templates → Create Template"
    echo "  3. 配置:"
    echo "     - Name: indextts2-service"
    echo "     - Docker Image: ghcr.io/jiyangnan/indextts2-service:latest"
    echo "     - GPU Type: NVIDIA RTX 3070 ⭐ (\$0.07/小时)"
    echo "     - Container Disk: 50GB"
    echo "     - Volume Disk: 20GB"
    echo "     - Ports: 8001 (HTTP)"
    echo "     - Env Vars:"
    echo "       MODEL_DIR=/app/checkpoints"
    echo "       USE_FP16=true"
    echo "       API_PORT=8001"
    echo "       SUPABASE_URL=https://dqpkhhyhnbvecpoeztwk.supabase.co"
    echo "       SUPABASE_SERVICE_KEY=<from backend .env>"
    echo "       SUPABASE_STORAGE_BUCKET=magictale"
    echo ""
    echo "  4. 保存模板并记录 Template ID"
    echo ""
    echo "设置环境变量: export RUNPOD_TEMPLATE_ID=template-xxx"
    exit 1
fi

echo -e "${BLUE}📋 启动配置:${NC}"
echo "  模板: $TEMPLATE_ID"
echo "  名称: $POD_NAME"
echo "  GPU: $GPU_COUNT x RTX 3070"
echo ""

# 启动 Pod
echo -e "${BLUE}🚀 启动 GPU 实例...${NC}"
RESPONSE=$(curl -s -X POST "https://api.runpod.io/v2/$TEMPLATE_ID/pods" \
  -H "Authorization: Bearer $RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"$POD_NAME\",
    \"gpuCount\": $GPU_COUNT,
    \"containerDiskInGb\": 50,
    \"volumeInGb\": 20,
    \"minMinutes\": $MINUTES
  }")

POD_ID=$(echo "$RESPONSE" | jq -r '.id')

if [ "$POD_ID" = "null" ] || [ -z "$POD_ID" ]; then
    echo -e "${RED}❌ Pod 启动失败${NC}"
    echo "$RESPONSE" | jq '.'
    exit 1
fi

echo -e "${GREEN}✅ Pod 启动成功!${NC}"
echo "  Pod ID: $POD_ID"
echo ""

# 等待 Pod 就绪
echo -e "${BLUE}⏳ 等待实例就绪...${NC}"
MAX_ATTEMPTS=30
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    STATUS_RESPONSE=$(curl -s "https://api.runpod.io/v2/pods/$POD_ID" \
      -H "Authorization: Bearer $RUNPOD_API_KEY" \
      -H "Content-Type: application/json")

    DESIRED_STATUS=$(echo "$STATUS_RESPONSE" | jq -r '.desiredStatus // "RUNNING"')
    CURRENT_STATUS=$(echo "$STATUS_RESPONSE" | jq -r '.runtime.currentStatus // "Unknown"')

    echo "  [$((ATTEMPT + 1))/$MAX_ATTEMPTS] 当前状态: $CURRENT_STATUS"

    if [ "$CURRENT_STATUS" = "RUNNING" ] && [ "$DESIRED_STATUS" = "RUNNING" ]; then
        echo -e "${GREEN}✅ 实例已就绪!${NC}"
        break
    fi

    if [ "$CURRENT_STATUS" = "FAILED" ] || [ "$CURRENT_STATUS" = "TERMINATED" ]; then
        echo -e "${RED}❌ 实例启动失败: $CURRENT_STATUS${NC}"
        echo "$STATUS_RESPONSE" | jq '.'
        exit 1
    fi

    sleep 10
    ATTEMPT=$((ATTEMPT + 1))
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
    echo -e "${YELLOW}⚠️  实例启动超时，请检查状态${NC}"
    echo "查看命令: curl -s \"https://api.runpod.io/v2/pods/$POD_ID\" \\"
    echo "  -H \"Authorization: Bearer \$RUNPOD_API_KEY\" | jq '.runtime'"
fi

# 获取 Pod 详情
POD_DETAILS=$(curl -s "https://api.runpod.io/v2/pods/$POD_ID" \
  -H "Authorization: Bearer $RUNPOD_API_KEY" \
  -H "Content-Type: application/json")

# 提取有用信息
POD_IP=$(echo "$POD_DETAILS" | jq -r '.runtime.ip // "Unknown"')
POD_PORT=$(echo "$POD_DETAILS" | jq -r '.runtime.ports[0].ipPort // "Unknown"')
POD_URL="http://$POD_IP:$POD_PORT"

echo ""
echo "======================================="
echo -e "${GREEN}🎉 Pod 运行中!${NC}"
echo "======================================="
echo "Pod ID: $POD_ID"
echo "Pod IP: $POD_IP"
echo "Pod Port: $POD_PORT"
echo "API URL: $POD_URL"
echo ""
echo "健康检查: curl $POD_URL/health"
echo "API 文档: $POD_URL/docs"
echo ""
echo -e "${YELLOW}💡 提示:${NC}"
echo "  停止实例: ./scripts/stop-runpod.sh $POD_ID"
echo "  查看日志: curl -s \"https://api.runpod.io/v2/pods/$POD_ID/logs\" \\"
echo "    -H \"Authorization: Bearer \$RUNPOD_API_KEY\""
echo ""

# 测试健康检查
echo -e "${BLUE}🔍 测试健康检查...${NC}"
sleep 5

HEALTH_RESPONSE=$(curl -s "$POD_URL/health" || echo "{}")

if echo "$HEALTH_RESPONSE" | jq -e '.status == "healthy"' > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 健康检查通过!${NC}"
    echo "$HEALTH_RESPONSE" | jq '.'
else
    echo -e "${YELLOW}⚠️  健康检查失败，可能需要更多时间启动${NC}"
    echo "响应: $HEALTH_RESPONSE"
fi

echo ""
echo -e "${GREEN}🚀 IndexTTS2 微服务已部署!${NC}"
