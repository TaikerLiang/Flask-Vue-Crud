import os
import random
import time
import logging
from typing import Any, Dict, List, Optional

import bezier
import numpy as np
import selenium.webdriver
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from seleniumwire.undetected_chromedriver import Chrome as WireUCChrome
from seleniumwire.webdriver import Chrome as WireChrome
from undetected_chromedriver import Chrome as UCChrome

from crawler.core.defines import BaseContentGetter
from crawler.core.proxy import ProxyManager
from crawler.plugin.plugin_loader import PluginLoader

logging.getLogger("seleniumwire").setLevel(logging.ERROR)
logging.getLogger("hpack").setLevel(logging.INFO)


class SeleniumContentGetter(BaseContentGetter):
    def __init__(
        self,
        proxy_manager: Optional[ProxyManager] = None,
        is_headless: bool = False,
        load_image: bool = True,
        need_anticaptcha: bool = False,
        block_urls: List = [],
    ):
        self._is_first = True
        running_at = os.environ.get("RUNNING_AT") or "scrapy"
        self.is_headless = is_headless and running_at == "scrapy"
        self._proxy_manager = proxy_manager
        self.load_image = load_image
        self.need_anticaptcha = need_anticaptcha
        self._driver = None
        self.profile_path = os.environ.get("PROFILE_PATH")
        chrome_version = os.environ.get("CHROME_VERSION")
        self.chrome_version = int(chrome_version) if chrome_version else None
        self.chromedriver_path = os.environ.get("CHROMEDRIVER_PATH")

    def get_current_url(self):
        return self._driver.current_url

    def scroll_to_bottom_of_page(self):
        self.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    def get_screenshot_as_file(self, filename: str):
        self._driver.get_screenshot_as_file(filename)

    def get_page_source(self):
        return self._driver.page_source

    def get_cookies(self):
        return self._driver.get_cookies()

    def get_cookies_dict(self) -> Dict:
        return {cookie_obj.get("name"): cookie_obj.get("value") for cookie_obj in self._driver.get_cookies()}

    def get_cookie_str(self):
        cookies_str = ""
        for key, value in self.get_cookies_dict().items():
            cookies_str += f"{key}={value}; "

        return cookies_str

    def get_num_of_tabs(self):
        return len(self._driver.window_handles)

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
        return alert.text

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

    def scroll_down(self, wait=True):
        self._driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        if wait:
            time.sleep(5)

    def scroll_up(self):
        self._driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(5)

    def wait_for_appear(self, css: str, wait_sec: int):
        locator = (By.CSS_SELECTOR, css)
        WebDriverWait(self._driver, wait_sec).until(EC.presence_of_element_located(locator))

    def slow_type(self, elem, page_input):
        for letter in page_input:
            time.sleep(float(random.uniform(0.05, 0.3)))
            elem.send_keys(letter)

    def click_mouse(self):
        import pyautogui
        pyautogui.click()

    def resting_mouse(self, end):  # move mouse to right of screen
        import pyautogui
        start = pyautogui.position()

        x2 = (start[0] + end[0]) / 3  # midpoint x
        y2 = (start[1] + end[1]) / 3  # midpoint y

        control1_X = (start[0] + x2) / 3
        control2_X = (end[0] + x2) / 3

        # Two intermediate control points that may be adjusted to modify the curve.
        control1 = control1_X, y2  # combine midpoints to create perfect curve
        control2 = control2_X, y2  # using y2 for both to get a more linear curve

        # Format points to use with bezier
        control_points = np.array([start, control1, control2, end])
        points = np.array([control_points[:, 0], control_points[:, 1]])  # Split x and y coordinates
        # You can set the degree of the curve here, should be less than # of control points
        degree = 3
        # Create the bezier curve
        curve = bezier.Curve(points, degree)

        curve_steps = (
            50  # How many points the curve should be split into. Each is a separate pyautogui.moveTo() execution
        )
        delay = 0.003  # Time between movements. 1/curve_steps = 1 second for entire curve

        # Move the mouse
        for j in range(1, curve_steps + 1):
            # The evaluate method takes a float from [0.0, 1.0] and returns the coordinates at that point in the curve
            # Another way of thinking about it is that i/steps gets the coordinates at (100*i/steps) percent into the curve
            x, y = curve.evaluate(j / curve_steps)
            pyautogui.moveTo(x, y)  # Move to point in curve
            pyautogui.sleep(delay)  # Wait delay


class ChromeContentGetter(SeleniumContentGetter):
    def __init__(
        self,
        proxy_manager: Optional[ProxyManager] = None,
        is_headless: bool = False,
        load_image: bool = True,
        need_anticaptcha: bool = False,
        block_urls: List = [],
    ):
        super().__init__(
            proxy_manager=proxy_manager,
            is_headless=is_headless,
            load_image=load_image,
            need_anticaptcha=need_anticaptcha,
            block_urls=block_urls,
        )

        options = selenium.webdriver.ChromeOptions()

        if self.need_anticaptcha:
            options = PluginLoader.load(plugin_name="anticaptcha", options=options)

        if self.is_headless:
            options.add_argument("--headless")
            options.add_argument(
                "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 11_1_0) AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/88.0.4324.96 Safari/537.36"
            )

        if not load_image:
            options.add_argument("blink-settings=imagesEnabled=false")  # 不加載圖片提高效率

        if self.profile_path:
            options.add_argument(f"--user-data-dir={self.profile_path}")

        options.add_argument("--disable-extensions")
        options.add_argument("--disable-notifications")
        options.add_argument("--enable-javascript")
        options.add_argument("--disable-gpu")  # 規避部分chrome gpu bug
        options.add_argument("--disable-dev-shm-usage")  # 使用共享內存RAM
        options.add_argument("--no-sandbox")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--allow-insecure-localhost")

        kwargs: dict[str, Any] = {
            "options": options,
        }

        if not self.is_headless:
            kwargs["version_main"] = self.chrome_version
            kwargs["driver_executable_path"] = self.chromedriver_path

        if proxy_manager:
            proxy_manager.renew_proxy()
            seleniumwire_options = {
                "proxy": {
                    "http": f"http://{proxy_manager.proxy_username}:{proxy_manager.proxy_password}@{proxy_manager.proxy_domain}",
                    "https": f"https://{proxy_manager.proxy_username}:{proxy_manager.proxy_password}@{proxy_manager.proxy_domain}",
                }
            }
            kwargs["seleniumwire_options"] = seleniumwire_options

        chrome_classes = [WireChrome, WireUCChrome] if proxy_manager else [Chrome, UCChrome]
        chrome_cls = chrome_classes[0] if self.is_headless else chrome_classes[1]
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
