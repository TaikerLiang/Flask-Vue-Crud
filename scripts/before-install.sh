#!/bin/bash
docker stop $(docker ps -a -q)
docker rm $(docker ps -a -q)
docker rmi $(docker images -q)
sudo rm -fr /home/ubuntu/flask-vue-crud
