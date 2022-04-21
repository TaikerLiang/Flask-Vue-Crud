import random
import time
from typing import Any, Dict, List, Optional

import selenium.webdriver
import seleniumwire.webdriver

from crawler.core.defines import BaseContentGetter
from crawler.core.proxy import ProxyManager


class SeleniumContentGetter(BaseContentGetter):
    def __init__(
        self,
        proxy_manager: Optional[ProxyManager] = None,
        is_headless: bool = False,
        load_image: bool = True,
        block_urls: List = [],
        profile_path: Optional[str] = None,
    ):
        self._is_first = True
        self.is_headless = is_headless
        self._proxy_manager = proxy_manager
        self.load_image = load_image
        self._driver = None
        self.profile_path = profile_path

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
        alert.text

    def execute_recaptcha_callback_fun(self, token: str):
        # ref: https://stackoverflow.com/questions/66476952/anti-captcha-not-working-validation-happening-before-callback-selenium
        # 1: go to your target url, inspect elements, click on console tab
        # 2: start typing: ___grecaptcha_cfg
        # 3: should check the path of the callback function would be different or not after a few days (TODO)
        self._driver.execute_script('document.getElementById("g-recaptcha-response").innerHTML = "{}";'.format(token))
        self._driver.execute_script(
            """
            jQuery('#btnLogin').prop('disabled', false);
            var response = grecaptcha.getResponse();
            jQuery('#hdnToken').val(response);
            """
        )
        time.sleep(2)


class ChromeContentGetter(SeleniumContentGetter):
    def __init__(
        self,
        proxy_manager: Optional[ProxyManager] = None,
        is_headless: bool = False,
        load_image: bool = True,
        block_urls: List = [],
        profile_path: Optional[str] = None,
    ):
        super().__init__(
            proxy_manager=proxy_manager,
            is_headless=is_headless,
            load_image=load_image,
            block_urls=block_urls,
            profile_path=profile_path,
        )

        options = selenium.webdriver.ChromeOptions()

        if self.is_headless:
            options.add_argument("--headless")

        if not load_image:
            options.add_argument("blink-settings=imagesEnabled=false")  # 不加載圖片提高效率

        if self.profile_path:
            options.add_argument(f"--user-data-dir={self.profile_path}")

        options.add_argument("--disable-extensions")
        options.add_argument("--disable-notifications")
        options.add_argument("--enable-javascript")
        options.add_argument("--disable-gpu")  # 規避部分chrome gpu bug
        options.add_argument(
            "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 11_1_0) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/88.0.4324.96 Safari/537.36"
        )
        options.add_argument("--disable-dev-shm-usage")  # 使用共享內存RAM
        options.add_argument("--no-sandbox")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--allow-insecure-localhost")
        # options.add_argument("auto-open-devtools-for-tabs")

        kwargs: dict[str, Any] = {
            "options": options,
        }
        if proxy_manager:
            proxy_manager.renew_proxy()
            seleniumwire_options = {
                "proxy": {
                    "http": f"http://{proxy_manager.proxy_username}:{proxy_manager.proxy_password}@{proxy_manager.proxy_domain}",
                    "https": f"https://{proxy_manager.proxy_username}:{proxy_manager.proxy_password}@{proxy_manager.proxy_domain}",
                }
            }
            kwargs["seleniumwire_options"] = seleniumwire_options

        chrome_cls = seleniumwire.webdriver.Chrome if proxy_manager else selenium.webdriver.Chrome
        self._driver = chrome_cls(**kwargs)

        default_block_urls = [
            "facebook.net/*",
            "www.google-analytics.com/*",
        ]

        self._driver.execute_cdp_cmd("Network.setBlockedURLs", {"urls": default_block_urls + block_urls})
        self._driver.execute_cdp_cmd("Network.enable", {})


class FirefoxContentGetter(SeleniumContentGetter):
    def __init__(
        self,
        service_log_path=None,
        proxy_manager: Optional[ProxyManager] = None,
        is_headless: bool = False,
        load_image: bool = True,
        block_urls: Optional[List] = None,
    ):
        super().__init__(
            proxy_manager=proxy_manager, is_headless=is_headless, load_image=load_image, block_urls=block_urls
        )

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
