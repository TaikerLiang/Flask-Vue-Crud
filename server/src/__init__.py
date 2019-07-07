from config import config
from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
# enable CORS
CORS(app, resources={r"/*": {"origins": "*"}})

from src import books
