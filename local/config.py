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
PROXY_URL = os.environ.get("PROXY_URL")
PROXY_PASSWORD = os.environ.get("PROXY_PASSWORD")
# For backwards compatibility, default version set to 98.
CHROME_VERSION = int(os.environ.get("CHROME_VERSION", "98"))
CHROMEDRIVER_PATH = os.environ.get("CHROMEDRIVER_PATH")
PROFILE_PATH = os.environ.get("PROFILE_PATH")


class ScreenColor:
    SUCCESS = "\033[92m"
    WARNING = "\033[93m"
    ERROR = "\033[91m"
