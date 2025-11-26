#!/usr/bin/env bash
set -euo pipefail

# 简单的 amd64 镜像打包脚本（使用 buildx）
# 用法:
#   ./build-amd64.sh [tag]
# 示例:
#   ./build-amd64.sh virtualwife-all:latest

TAG="${1:-virtualwife-all:latest}"

echo "=> ensure buildx builder"
if ! docker buildx inspect multiarch-builder >/dev/null 2>&1; then
  docker buildx create --name multiarch-builder --use
else
  docker buildx use multiarch-builder
fi

echo "=> building for linux/amd64, tag=${TAG}"
DOCKER_BUILDKIT=1 docker buildx build \
  --platform linux/amd64 \
  -t "${TAG}" \
  --load \
  .

echo "=> done. image tagged as ${TAG}"
