#!/bin/bash
git fetch
git reset --hard origin/master
python3 local_crawler.py
