from config import config
from flask import Flask
import os

app = Flask(__name__)

try:
    app.config.from_object(config[os.getenv("ENV")])
    _evn = os.getenv("ENV")
except:
    app.config.from_object(config["default"])
    _evn = "dev"

app.logger.error(os.getenv("ENV"))

from src import books