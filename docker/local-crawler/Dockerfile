FROM debian:stable

RUN apt-get update && apt-get install -y xvfb chromium-common=99.0.4844.74-1~deb11u1 chromium=99.0.4844.74-1~deb11u1 python3 python3-pip python3-tk python3-dev
COPY ./requirements-dev-linux.txt /root/requirements-dev.txt
RUN pip3 install -r /root/requirements-dev.txt

# Fetch chromedriver
RUN apt-get install -y wget unzip
RUN mkdir -p /root/temp
RUN wget https://chromedriver.storage.googleapis.com/99.0.4844.51/chromedriver_linux64.zip -O /root/temp/chromedriver.zip
RUN unzip /root/temp/chromedriver.zip -d /usr/local/bin
RUN rm /root/temp/chromedriver.zip

COPY . /root
WORKDIR /root/local
CMD xvfb-run -s "-screen 0 1920x1200x24" python3 local_crawler.py -m prd
