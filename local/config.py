import os
import sys

from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.abspath("..")))
sys.path.append(os.path.join(os.path.abspath("../src")))
sys.path.append(os.path.join(os.path.abspath("seleniumwire")))

load_dotenv()

EDI_USER = os.environ.get("EDI_ENGINE_USER")
EDI_TOKEN = os.environ.get("EDI_ENGINE_TOKEN")
EDI_DOMAIN = os.environ.get("EDI_ENGINE_DOMAIN")


class ScreenColor:
    SUCCESS = "\033[92m"
    WARNING = "\033[93m"
    ERROR = "\033[91m"
