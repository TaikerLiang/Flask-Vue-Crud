#!/bin/bash
cd /home/ubuntu/flask-vue-crud
echo "DOCKER_REGISTRY=364135942435.dkr.ecr.ap-northeast-1.amazonaws.com/xinyisheng-erp" >> .env
echo "BRANCH="$DEPLOYMENT_GROUP_NAME >> .env
