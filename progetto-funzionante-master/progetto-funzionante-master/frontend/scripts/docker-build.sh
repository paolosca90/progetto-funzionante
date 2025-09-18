#!/bin/bash

# Docker Build Script for Trading System
# This script builds optimized Docker images with multiple targets

set -euo pipefail

# Configuration
IMAGE_NAME="trading-system-api"
REGISTRY=${REGISTRY:-"docker.io"}
DOCKER_USER=${DOCKER_USER:-""}
VERSION=${VERSION:-"latest"}
BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
VCS_REF=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --target)
            TARGET="$2"
            shift 2
            ;;
        --push)
            PUSH=true
            shift
            ;;
        --platform)
            PLATFORM="$2"
            shift 2
            ;;
        --cache)
            CACHE_TYPE="$2"
            shift 2
            ;;
        --version)
            VERSION="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --target TARGET     Build target (builder, production, test)"
            echo "  --push              Push image to registry"
            echo "  --platform PLATFORM Build for specific platform (linux/amd64, linux/arm64)"
            echo "  --cache CACHE_TYPE  Cache type (local, registry, none)"
            echo "  --version VERSION   Image version tag"
            echo "  --help              Show this help message"
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Set defaults
TARGET=${TARGET:-"production"}
PUSH=${PUSH:-false}
PLATFORM=${PLATFORM:-"linux/amd64"}
CACHE_TYPE=${CACHE_TYPE:-"local"}

# Build arguments
BUILD_ARGS=(
    --build-arg BUILD_DATE="$BUILD_DATE"
    --build-arg VCS_REF="$VCS_REF"
    --build-arg VERSION="$VERSION"
)

# Add target if specified
if [[ -n "$TARGET" ]]; then
    BUILD_ARGS+=(--target "$TARGET")
fi

# Add platform if specified
if [[ -n "$PLATFORM" ]]; then
    BUILD_ARGS+=(--platform "$PLATFORM")
fi

# Add cache configuration
case "$CACHE_TYPE" in
    "local")
        BUILD_ARGS+=(--cache-from=type=local,src=/tmp/.buildx-cache)
        BUILD_ARGS+=(--cache-to=type=local,dest=/tmp/.buildx-cache-new,mode=max)
        ;;
    "registry")
        BUILD_ARGS+=(--cache-from=type=registry,ref="$DOCKER_USER/$IMAGE_NAME:buildcache")
        BUILD_ARGS+=(--cache-to=type=registry,ref="$DOCKER_USER/$IMAGE_NAME:buildcache,mode=max")
        ;;
    "none")
        BUILD_ARGS+=(--no-cache)
        ;;
esac

# Full image name
FULL_IMAGE_NAME="$IMAGE_NAME"
if [[ -n "$DOCKER_USER" ]]; then
    FULL_IMAGE_NAME="$DOCKER_USER/$IMAGE_NAME"
fi
FULL_IMAGE_NAME="$FULL_IMAGE_NAME:$VERSION"

log "Building Docker image..."
log "Image: $FULL_IMAGE_NAME"
log "Target: $TARGET"
log "Platform: $PLATFORM"
log "Cache: $CACHE_TYPE"

# Check if Docker Buildx is available
if ! docker buildx version >/dev/null 2>&1; then
    error "Docker Buildx is not available"
    exit 1
fi

# Create buildx builder if it doesn't exist
if ! docker buildx inspect trading-builder >/dev/null 2>&1; then
    log "Creating Docker Buildx builder..."
    docker buildx create --name trading-builder --use
fi

# Build the image
log "Starting build process..."
docker buildx build \
    "${BUILD_ARGS[@]}" \
    --tag "$FULL_IMAGE_NAME" \
    --label "org.opencontainers.image.created=$BUILD_DATE" \
    --label "org.opencontainers.image.revision=$VCS_REF" \
    --label "org.opencontainers.image.version=$VERSION" \
    --label "maintainer=Trading System Team" \
    . \
    ${PUSH:+--push}

if [[ $? -eq 0 ]]; then
    log "Build completed successfully!"

    # Show image size
    IMAGE_SIZE=$(docker images "$FULL_IMAGE_NAME" --format "table {{.Size}}" | tail -n 1)
    log "Image size: $IMAGE_SIZE"

    # Push to registry if requested
    if [[ "$PUSH" == true ]]; then
        log "Pushing image to registry..."
        docker push "$FULL_IMAGE_NAME"
        log "Image pushed successfully!"
    fi

    # Tag as latest if this is a versioned build
    if [[ "$VERSION" != "latest" ]]; then
        LATEST_TAG="$FULL_IMAGE_NAME"
        LATEST_TAG="${LATEST_TAG%:*}:latest"
        docker tag "$FULL_IMAGE_NAME" "$LATEST_TAG"

        if [[ "$PUSH" == true ]]; then
            log "Pushing latest tag..."
            docker push "$LATEST_TAG"
        fi
    fi
else
    error "Build failed!"
    exit 1
fi

# Cache cleanup for local cache
if [[ "$CACHE_TYPE" == "local" ]]; then
    log "Cleaning up build cache..."
    rm -rf /tmp/.buildx-cache
    mv /tmp/.buildx-cache-new /tmp/.buildx-cache 2>/dev/null || true
fi

log "Build process completed!"
exit 0