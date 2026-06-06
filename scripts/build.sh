#!/usr/bin/env bash
# Build the autonomy-stack Docker image.
# Usage: bash scripts/build.sh [x86|arm64] [tag]
set -euo pipefail

PLATFORM="${1:-x86}"
TAG="${2:-autonomy-stack:latest}"

case "${PLATFORM}" in
    arm64|jetson)
        DOCKERFILE="docker/Dockerfile.arm64"
        BUILD_PLATFORM="linux/arm64"
        ;;
    x86|amd64|*)
        DOCKERFILE="docker/Dockerfile.x86"
        BUILD_PLATFORM="linux/amd64"
        ;;
esac

echo "Building ${TAG} | platform=${BUILD_PLATFORM} | dockerfile=${DOCKERFILE}"

docker buildx build \
    --platform "${BUILD_PLATFORM}" \
    --file "${DOCKERFILE}" \
    --tag "${TAG}" \
    --load \
    .

echo "Done: ${TAG}"
