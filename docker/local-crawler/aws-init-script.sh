#!/bin/bash
# Remember to replace IMAGE_TAG, EDI_ENGINE_DOMAIN, EDI_ENGINE_USER and EDI_ENGINE_TOKEN to correct value.
rm -f /home/ubuntu/.env
echo IMAGE_TAG=latest >> /home/ubuntu/.env
echo EDI_ENGINE_DOMAIN=YOUR_DOMAIN >> /home/ubuntu/.env
echo EDI_ENGINE_USER=YOUR_USER >> /home/ubuntu/.env
echo EDI_ENGINE_TOKEN=YOUR_TOKEN >> /home/ubuntu/.env
sudo systemctl is-active --quiet ep-sc || sudo systemctl start ep-sc
