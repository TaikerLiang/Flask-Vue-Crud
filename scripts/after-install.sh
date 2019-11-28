#!/bin/bash
sudo chown -R ubuntu:root /home/ubuntu/flask-vue-crud
cd /home/ubuntu/flask-vue-crud
sudo mv ../.env ./.env
docker-compose pull
docker-compose up -d
