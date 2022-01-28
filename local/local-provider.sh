#!/bin/bash
git fetch
git reset --hard origin/master
pip3 install -r ../requirements-dev.txt
python3 local_crawler.py
