#!/usr/bin/env bash

set -euo pipefail

AWS_ECR="478041131377.dkr.ecr.us-west-2.amazonaws.com"
LOCAL_CRAWLER_REPO="hardcore/ep-sc-local-crawler"

TAG=${TAG_NAME:-$(git describe --always --tags)}
VCS_REF=$(git rev-parse --short HEAD)
export TAG
export VCS_REF


# ========================================================================
# Retrieve an authentication token and authenticate to your registry
# ========================================================================
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin $AWS_ECR


# ========================================================================
# Push Docker Image to ECR
# ========================================================================
echo "Pushing image $AWS_ECR/$LOCAL_CRAWLER_REPO:$VCS_REF to ECR ..."
docker tag "$LOCAL_CRAWLER_REPO:$VCS_REF" "$AWS_ECR/$LOCAL_CRAWLER_REPO:$VCS_REF"
docker push "$AWS_ECR/$LOCAL_CRAWLER_REPO:$VCS_REF"

echo "Pushing image $AWS_ECR/$LOCAL_CRAWLER_REPO:$TAG to ECR ..."
docker tag "$LOCAL_CRAWLER_REPO:$VCS_REF" "$AWS_ECR/$LOCAL_CRAWLER_REPO:$TAG"
docker push "$AWS_ECR/$LOCAL_CRAWLER_REPO:$TAG"

echo "Pushing image $AWS_ECR/$LOCAL_CRAWLER_REPO:latest to ECR ..."
docker tag "$LOCAL_CRAWLER_REPO:$VCS_REF" "$AWS_ECR/$LOCAL_CRAWLER_REPO:latest"
docker push "$AWS_ECR/$LOCAL_CRAWLER_REPO:latest"
