FROM python:3.7.3-stretch

# set working directory
WORKDIR '/app'

COPY ./requirements.txt ./
RUN pip install -r requirements.txt

COPY . .

# Expose the port uWSGI will listen on
EXPOSE 8000

CMD ["gunicorn", "-b", "0.0.0.0:8000", "run:app"]