FROM python:3.7.3-stretch

ARG ENV
ENV ENV=${ENV}

# set working directory
WORKDIR '/app'

COPY ./requirements.txt ./
RUN pip install -r requirements.txt

COPY . .

# Expose the port uWSGI will listen on
EXPOSE 8000

CMD gunicorn -b 0.0.0.0:8000 -e ENV=${ENV} --workers=1 --worker-class=gthread run:app
#CMD ["gunicorn", "-b", "0.0.0.0:8000", "--worker-tmp-dir", "/dev/shm", "--workers=2", "--threads=4", "--worker-class=gthread", "run:app"]