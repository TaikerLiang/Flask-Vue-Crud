#!/bin/bash

cd /home/ubuntu/flask-vue-crud
sudo cp -r .env ../
sudo rm -fr /home/ubuntu/flask-vue-crud
docker-compose down
docker rm $(docker ps -a -q)
docker rmi $(docker images -q)