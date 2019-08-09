from config import config
from flask import Flask

app = Flask(__name__)

from src import books
