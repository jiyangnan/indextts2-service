#!/bin/bash
# RunPod 部署编排脚本 - 构建、推送、启动

set -e

# 配置
IMAGE_NAME="${IMAGE_NAME:-ghcr.io/jiyangnan/indextts2-service}"
IMAGE_TAG="${IMAGE_TAG:-v2.0.0}"

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

FULL_IMAGE="$IMAGE_NAME:$IMAGE_TAG"

echo "======================================="
echo "🚀 IndexTTS2 微服务部署脚本"
echo "======================================="
echo "镜像: $FULL_IMAGE"
echo "GPU: RTX 3070 (\$0.07/小时) ⭐"
echo ""

# 1. 检查 GitHub PAT
if [ -z "$GITHUB_PAT" ]; then
    echo -e "${RED}❌ 未设置 GITHUB_PAT 环境变量${NC}"
    echo ""
    echo "请先设置 GitHub Personal Access Token:"
    echo "  1. 访问: https://github.com/settings/tokens"
    echo "  2. 生成新的 Token (需要 write:packages 权限)"
    echo "  3. 设置: export GITHUB_PAT=your_token"
    exit 1
fi

# 2. 登录 GHCR
echo -e "${BLUE}🔐 登录 GitHub Container Registry...${NC}"
echo "$GITHUB_PAT" | docker login ghcr.io -u jiyangnan --password-stdin > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ GHCR 登录成功${NC}"
else
    echo -e "${RED}❌ GHCR 登录失败${NC}"
    echo "请检查 GITHUB_PAT 是否正确"
    exit 1
fi
echo ""

# 3. 构建镜像
echo -e "${BLUE}📦 构建 Docker 镜像...${NC}"
docker build -t "$FULL_IMAGE" .

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ 镜像构建失败${NC}"
    exit 1
fi

# 同时打 latest 标签
docker tag "$FULL_IMAGE" "$IMAGE_NAME:latest"
echo -e "${GREEN}✅ 镜像构建完成${NC}"
echo ""

# 4. 推送镜像
echo -e "${BLUE}⬆️  推送镜像到 GHCR...${NC}"
docker push "$FULL_IMAGE"
docker push "$IMAGE_NAME:latest"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ 镜像推送失败${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 镜像推送完成${NC}"
echo ""
echo -e "${YELLOW}📦 查看镜像: https://github.com/jiyangnan?tab=packages${NC}"
echo ""

# 5. 检查 RunPod API Key
if [ -z "$RUNPOD_API_KEY" ]; then
    echo -e "${YELLOW}⚠️  未设置 RUNPOD_API_KEY${NC}"
    echo ""
    echo "如需启动 RunPod 实例，请设置:"
    echo "  export RUNPOD_API_KEY=rpa_xxx..."
    echo ""
    echo "然后运行:"
    echo "  ./scripts/start-runpod.sh"
    echo ""
    exit 0
fi

# 6. 启动 Pod
echo -e "${BLUE}🚀 启动 RunPod 实例...${NC}"
./scripts/start-runpod.sh

echo ""
echo -e "${GREEN}🎉 部署完成!${NC}"
