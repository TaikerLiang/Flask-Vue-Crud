#!/bin/bash
#git fetch
#git reset --hard origin/master
#pip3 install -r ../requirements-dev.txt
while true
do
  timeout 1800 python3 local_crawler.py -m prd
  pkill -9 -f google
  sleep 10
done
