import random
from typing import Dict

# from selenium import webdriver
from seleniumwire import webdriver

from crawler.core.defines import BaseContentGetter


class SeleniumContentGetter(BaseContentGetter):
    def __init__(self, proxy_manager: None, is_headless: bool = False):
        self._is_first = True
        self.is_headless = is_headless
        self._proxy_manager = proxy_manager
        self._driver = None

    def get_current_url(self):
        return self._driver.current_url

    def scroll_to_bottom_of_page(self):
        self.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    def get_page_source(self):
        return self._driver.page_source

    def get_cookies(self):
        return self._driver.get_cookies()

    def get_cookies_dict(self) -> Dict:
        return {cookie_obj.get("name"): cookie_obj.get("value") for cookie_obj in self._driver.get_cookies()}

    def execute_script(self, script: str):
        self._driver.execute_script(script)

    def quit(self):
        self._driver.quit()

    def page_refresh(self):
        self._driver.refresh()

    def close(self):
        self._driver.close()

    def check_alert(self):
        alert = self._driver.switch_to.alert
        text = alert.text


class ChromeContentGetter(SeleniumContentGetter):
    def __init__(self, proxy_manager: None, is_headless: bool = False):
        super().__init__(proxy_manager=proxy_manager, is_headless=is_headless)

        options = webdriver.ChromeOptions()

        if self.is_headless:
            options.add_argument("--headless")

        options.add_argument("--disable-extensions")
        options.add_argument("--disable-notifications")
        options.add_argument("--enable-javascript")
        options.add_argument("--disable-gpu")
        options.add_argument(
            f"user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 11_1_0) AppleWebKit/537.36 (KHTML, like Gecko) "
            f"Chrome/88.0.4324.96 Safari/537.36"
        )
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-blink-features=AutomationControlled")

        seleniumwire_options = {
            "proxy": {
                "http": "http://gofr13759lcdh32673:17r6FJjK3x8IQKP3@isp2.hydraproxy.com:9989",
                "https": "https://gofr13759lcdh32673:17r6FJjK3x8IQKP3@isp2.hydraproxy.com:9989",
            }
        }

        self._driver = webdriver.Chrome(chrome_options=options, seleniumwire_options=seleniumwire_options)
        self._driver.execute_cdp_cmd(
            "Network.setBlockedURLs", {"urls": ["facebook.net/*", "www.google-analytics.com/*"]}
        )
        self._driver.execute_cdp_cmd("Network.enable", {})


class FirefoxContentGetter(SeleniumContentGetter):
    def __init__(self, service_log_path=None):
        super().__init__()

        useragent = self._random_choose_user_agent()
        profile = webdriver.FirefoxProfile()
        profile.set_preference("general.useragent.override", useragent)
        options = webdriver.FirefoxOptions()

        if self.is_headless:
            options.add_argument("--headless")

        options.set_preference("dom.webnotifications.serviceworker.enabled", False)
        options.set_preference("dom.webnotifications.enabled", False)

        self._driver = webdriver.Firefox(firefox_profile=profile, options=options, service_log_path=service_log_path)

    @staticmethod
    def _random_choose_user_agent():
        user_agents = [
            # firefox
            ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:80.0) " "Gecko/20100101 " "Firefox/80.0"),
            ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:79.0) " "Gecko/20100101 " "Firefox/79.0"),
            ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:78.0) " "Gecko/20100101 " "Firefox/78.0"),
            ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:78.0.1) " "Gecko/20100101 " "Firefox/78.0.1"),
        ]

        return random.choice(user_agents)
