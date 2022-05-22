#!/usr/bin/env bash

set -euo pipefail

LOCAL_CRAWLER_REPO="hardcore/ep-sc-local-crawler"

TAG=$(git describe --always --tags)
VCS_REF=$(git rev-parse --short HEAD)
export TAG
export VCS_REF

REPO_ROOT=$( cd "$( dirname "${BASH_SOURCE[0]}" )/../../" && pwd )
declare -xr REPO_ROOT
cd "$REPO_ROOT"

# ========================================================================
# Build Docker Image
# ========================================================================
if docker image inspect "$LOCAL_CRAWLER_REPO:$VCS_REF" > /dev/null 2>&1; then
    echo "$LOCAL_CRAWLER_REPO:$VCS_REF image exists"
else
    echo "Building image $LOCAL_CRAWLER_REPO:$VCS_REF ..."

    docker build \
        -f docker/local-crawler/Dockerfile \
        -t "$LOCAL_CRAWLER_REPO:$VCS_REF" \
        --build-arg VERSION="${TAG}" \
        --build-arg VCS_REF="${VCS_REF}" .
fi
