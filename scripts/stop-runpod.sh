#!/bin/bash
# RunPod 停止脚本

set -e

POD_ID="$1"

if [ -z "$POD_ID" ]; then
    echo "用法: $0 <pod_id>"
    exit 1
fi

if [ -z "$RUNPOD_API_KEY" ]; then
    echo "⚠️  未设置 RUNPOD_API_KEY 环境变量"
    exit 1
fi

echo "🛑 停止 GPU 实例: $POD_ID"

RESPONSE=$(curl -s -X POST "https://api.runpod.io/v2/pods/$POD_ID/terminate" \
  -H "Authorization: Bearer $RUNPOD_API_KEY")

echo "$RESPONSE" | jq '.'

echo "✅ 实例已停止"
