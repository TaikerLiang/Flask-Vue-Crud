FROM scrapinghub/scrapinghub-stack-scrapy:2.0

RUN set -ex \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        unzip \
        xvfb \
        python3-tk \
        python3-dev


#============================================
# Google Chrome
#============================================
# can specify versions by CHROME_VERSION;
#  e.g. google-chrome-stable=53.0.2785.101-1
#       google-chrome-beta=53.0.2785.92-1
#       google-chrome-unstable=54.0.2840.14-1
#       latest (equivalent to google-chrome-stable)
#       google-chrome-beta  (pull latest beta)
#============================================
ARG CHROME_VERSION="google-chrome-stable"
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
  && echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
  && apt-get update -qqy \
  && apt-get -qqy install \
    ${CHROME_VERSION:-google-chrome-stable} \
  && rm /etc/apt/sources.list.d/google-chrome.list \
  && rm -rf /var/lib/apt/lists/* /var/cache/apt/*


#============================================
# Chrome Webdriver
#============================================
# can specify versions by CHROME_DRIVER_VERSION
# Latest released version will be used by default
#============================================
ARG CHROME_DRIVER_VERSION
RUN CHROME_STRING=$(google-chrome --version) \
  && CHROME_VERSION_STRING=$(echo "${CHROME_STRING}" | grep -oP "\d+\.\d+\.\d+\.\d+") \
  && CHROME_MAYOR_VERSION=$(echo "${CHROME_VERSION_STRING%%.*}") \
  && wget --no-verbose -O /tmp/LATEST_RELEASE "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_MAYOR_VERSION}" \
  && CD_VERSION=$(cat "/tmp/LATEST_RELEASE") \
  && rm /tmp/LATEST_RELEASE \
  && if [ -z "$CHROME_DRIVER_VERSION" ]; \
     then CHROME_DRIVER_VERSION="${CD_VERSION}"; \
     fi \
  && CD_VERSION=$(echo $CHROME_DRIVER_VERSION) \
  && echo "Using chromedriver version: "$CD_VERSION \
  && wget --no-verbose -O /tmp/chromedriver_linux64.zip https://chromedriver.storage.googleapis.com/$CD_VERSION/chromedriver_linux64.zip \
  && rm -rf /opt/selenium/chromedriver \
  && unzip /tmp/chromedriver_linux64.zip -d /opt/selenium \
  && rm /tmp/chromedriver_linux64.zip \
  && mv /opt/selenium/chromedriver /opt/selenium/chromedriver-$CD_VERSION \
  && chmod 755 /opt/selenium/chromedriver-$CD_VERSION \
  && sudo ln -fs /opt/selenium/chromedriver-$CD_VERSION /usr/local/bin/chromedriver


#============================================
# Firefox & Geckodriver
#============================================

RUN sudo apt-get update \
    && sudo apt-get install -y firefox-esr

RUN wget https://github.com/mozilla/geckodriver/releases/download/v0.30.0/geckodriver-v0.30.0-linux64.tar.gz \
    && sudo sh -c 'tar -x geckodriver -zf geckodriver-v0.30.0-linux64.tar.gz -O > /usr/bin/geckodriver' \
    && sudo chmod +x /usr/bin/geckodriver \
    && rm geckodriver-v0.30.0-linux64.tar.gz

#============================================
# chromium
#============================================
RUN apt-get install libxss1
RUN wget -O /tmp/chrome-linux.zip https://storage.googleapis.com/chromium-browser-snapshots/Linux_x64/588429/chrome-linux.zip
RUN mkdir -p ~/.local/share/pyppeteer/local-chromium/588429/
RUN unzip /tmp/chrome-linux.zip -d ~/.local/share/pyppeteer/local-chromium/588429/

ENV OPENSSL_CONF=/etc/ssl/
ENV TERM xterm
ENV SCRAPY_SETTINGS_MODULE crawler.settings

RUN mkdir -p /app
WORKDIR /app
COPY ./requirements-app.txt /app/requirements.txt
RUN pip install pyautogui # PyObjC issue
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app
RUN python setup.py install

ARG EDI_ENGINE_BASE_URL
ARG EDI_ENGINE_USER
ARG EDI_ENGINE_TOKEN
ARG EDI_HOST
ENV EDI_ENGINE_BASE_URL=${EDI_ENGINE_BASE_URL}
ENV EDI_ENGINE_USER=${EDI_ENGINE_USER}
ENV EDI_ENGINE_TOKEN=${EDI_ENGINE_TOKEN}
ENV EDI_HOST=${EDI_HOST}


# run scrapy by 'docker run $DOCKER_NAME shub-image-info'
