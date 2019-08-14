from config import config
from flask import Flask

app = Flask(__name__)

try:
    app.config.from_object(config[os.getenv("ENV")])
    _evn = os.getenv("ENV")
except:
    app.config.from_object(config["default"])
    _evn = "dev"

from src import books