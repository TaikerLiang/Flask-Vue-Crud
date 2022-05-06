import logging
from pathlib import Path

from selenium.webdriver import ChromeOptions

logger = logging.getLogger("plugin_loader")


class PluginLoader:
    @staticmethod
    def load(plugin_name: str, options: ChromeOptions):
        logger.info("Loading anticaptcha plugin ...")
        file = Path(f"./plugin/{plugin_name}/")
        if file.is_dir() and file.exists():
            options.add_argument(f"--load-extension=./plugin/{plugin_name}")
        else:
            raise RuntimeError(f"Plugin folder '{plugin_name}' missing")

        return options
