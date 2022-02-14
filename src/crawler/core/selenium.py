import random
from typing import Dict, Optional
from crawler.core.proxy import ProxyManager

import selenium.webdriver
import seleniumwire.webdriver

from crawler.core.defines import BaseContentGetter


class SeleniumContentGetter(BaseContentGetter):
    def __init__(
        self, proxy_manager: Optional[ProxyManager] = None, is_headless: bool = False, load_image: bool = True
    ):
        self._is_first = True
        self.is_headless = is_headless
        self._proxy_manager = proxy_manager
        self.load_image = load_image
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

    def switch_to_last_window(self):
        windows = self._driver.window_handles
        self._driver.switch_to.window(windows[-1])

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
    def __init__(
        self, proxy_manager: Optional[ProxyManager] = None, is_headless: bool = False, load_image: bool = True
    ):
        super().__init__(proxy_manager=proxy_manager, is_headless=is_headless, load_image=load_image)

        options = selenium.webdriver.ChromeOptions()

        if self.is_headless:
            options.add_argument("--headless")

        if not load_image:
            options.add_argument("blink-settings=imagesEnabled=false")  # 不加載圖片提高效率

        options.add_argument("--disable-extensions")
        options.add_argument("--disable-notifications")
        options.add_argument("--enable-javascript")
        options.add_argument("--disable-gpu")  # 規避部分chrome gpu bug
        options.add_argument(
            f"user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 11_1_0) AppleWebKit/537.36 (KHTML, like Gecko) "
            f"Chrome/88.0.4324.96 Safari/537.36"
        )
        options.add_argument("--disable-dev-shm-usage")  # 使用共享內存RAM
        options.add_argument("--no-sandbox")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-blink-features=AutomationControlled")

        if proxy_manager:
            proxy_manager.renew_proxy()
            seleniumwire_options = {
                "proxy": {
                    "http": f"http://{proxy_manager.proxy_username}:{proxy_manager.proxy_password}@{proxy_manager.proxy_domain}",
                    "https": f"https://{proxy_manager.proxy_username}:{proxy_manager.proxy_password}@{proxy_manager.proxy_domain}",
                }
            }
            self._driver = seleniumwire.webdriver.Chrome(
                chrome_options=options, seleniumwire_options=seleniumwire_options
            )
        else:
            self._driver = selenium.webdriver.Chrome(chrome_options=options)

        self._driver.execute_cdp_cmd(
            "Network.setBlockedURLs", {"urls": ["facebook.net/*", "www.google-analytics.com/*"]}
        )
        self._driver.execute_cdp_cmd("Network.enable", {})


class FirefoxContentGetter(SeleniumContentGetter):
    def __init__(self, service_log_path=None, is_headless: bool = False):
        super().__init__(is_headless=is_headless)

        useragent = self._random_choose_user_agent()
        profile = selenium.webdriver.FirefoxProfile()
        profile.set_preference("general.useragent.override", useragent)
        options = selenium.webdriver.FirefoxOptions()

        if self.is_headless:
            options.add_argument("--headless")

        options.set_preference("dom.webnotifications.serviceworker.enabled", False)
        options.set_preference("dom.webnotifications.enabled", False)

        self._driver = selenium.webdriver.Firefox(
            firefox_profile=profile, options=options, service_log_path=service_log_path
        )

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
