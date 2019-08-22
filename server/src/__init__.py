from config import config
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

try:
    app.config.from_object(config[os.getenv("ENV")])
    _evn = os.getenv("ENV")
except:
    app.config.from_object(config["default"])
    _evn = "dev"

app.logger.info(os.getenv("ENV"))
print(app.config['SQLALCHEMY_DATABASE_URI'])

db = SQLAlchemy(app)

from src import books