eval $(aws ecr get-login --no-include-email --region ap-northeast-1)
cd /home/ubuntu/flask-vue-crud
docker-compose pull
docker-compose up -d 