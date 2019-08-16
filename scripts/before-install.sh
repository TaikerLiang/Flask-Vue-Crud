#!/bin/bash

cd /home/ubuntu/flask-vue-crud
docker-compose down
sudo cp -r .env ../
cd ~
sudo rm -fr /home/ubuntu/flask-vue-crud
#docker rm $(docker ps -a -q)
#docker rmi $(docker images -q)