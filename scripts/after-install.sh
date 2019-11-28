#!/bin/bash
cd /home/ubuntu/flask-vue-crud
echo "DOCKER_REGISTRY=979007176950.dkr.ecr.ap-northeast-1.amazonaws.com/flask-vue-crud" >> .env
echo "BRANCH="$DEPLOYMENT_GROUP_NAME >> .env
