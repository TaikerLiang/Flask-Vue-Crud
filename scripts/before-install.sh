#!/bin/bash
sudo chown -R ubuntu:root /home/ubuntu/flask-vue-crud
docker stop $(docker ps -a -q)
docker rm $(docker ps -a -q)
docker rmi $(docker images -q)
sudo rm -fr /home/ubuntu/flask-vue-crud
