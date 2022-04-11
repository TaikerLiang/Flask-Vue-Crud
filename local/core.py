import abc
import dataclasses
import logging
import random
import string
import time

import bezier
import numpy as np
import pyautogui
from scrapy import Request
from scrapy.http import TextResponse
import selenium.webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from seleniumwire.undetected_chromedriver.v2 import Chrome
import undetected_chromedriver as us

from local.config import PROXY_PASSWORD, PROXY_URL
from local.proxy import HydraproxyProxyManager

logger = logging.getLogger("seleniumwire")
logger.setLevel(logging.ERROR)


@dataclasses.dataclass
class CompanyInfo:
    lower_short: str
    upper_short: str
    email: str
    password: str


@dataclasses.dataclass
class ProxyOption:
    group: str
    session: str


class BaseSeleniumContentGetter:
    PROXY_URL = PROXY_URL
    PROXY_PASSWORD = PROXY_PASSWORD

    def __init__(self, proxy: bool):
        seleniumwire_options = {}
        options = selenium.webdriver.ChromeOptions()

        options.add_argument("--disable-dev-shm-usage")  # 使用共享內存RAM
        options.add_argument("--no-sandbox")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-blink-features=AutomationControlled")
        self.proxy = proxy
        if self.proxy:
            proxy_manager = HydraproxyProxyManager(logger=logger)
            proxy_manager.renew_proxy()
            seleniumwire_options = {
                "proxy": {
                    "http": f"http://{proxy_manager.proxy_username}:{proxy_manager.proxy_password}@{proxy_manager.PROXY_DOMAIN}",
                    "https": f"https://{proxy_manager.proxy_username}:{proxy_manager.proxy_password}@{proxy_manager.PROXY_DOMAIN}",
                }
            }
            self.driver = Chrome(version_main=98, seleniumwire_options=seleniumwire_options, options=options)
        else:
            self.driver = us.Chrome(version_main=98, options=options)
        # self.driver.get("https://nowsecure.nl")
        # time.sleep(5)
        self.action = ActionChains(self.driver)

    def go_to(self, url: str, seconds: int):
        self.driver.get(url=url)
        time.sleep(seconds)

    def delete_all_cookies(self):
        self.driver.delete_all_cookies()

    def execute_script(self, script: str):
        self.driver.execute_script(script=script)

    def get_cookies(self):
        return self.driver.get_cookies()

    def save_screenshot(self, file_name: str):
        self.driver.save_screenshot(file_name)

    def quit(self):
        self.driver.quit()

    def close(self):
        self.driver.close()

    def scroll_down(self):
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(5)

    def scroll_up(self):
        self.driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(5)

    def back_to_previous(self):
        self.driver.back()
        time.sleep(2)

    def find_element_by_css_selector(self, css: str):
        return self.driver.find_element_by_css_selector(css_selector=css)

    def wait_for_appear(self, css: str, wait_sec: int):
        locator = (By.CSS_SELECTOR, css)
        WebDriverWait(self.driver, wait_sec).until(EC.presence_of_element_located(locator))

    def resting_mouse(self):  # move mouse to right of screen

        start = pyautogui.position()
        end = random.randint(1600, 1750), random.randint(400, 850)

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
        time.sleep(2)

    def slow_type(self, elem, page_input):
        for letter in page_input:
            time.sleep(float(random.uniform(0.05, 0.3)))
            elem.send_keys(letter)

    def move_mouse_to_random_position(self):
        max_x, max_y = self.driver.execute_script("return [window.innerWidth, window.innerHeight];")
        body = self.driver.find_element_by_tag_name("body")
        actions = ActionChains(self.driver)
        x = random.randint(0, max_x)
        y = random.randint(0, max_y)
        actions.move_to_element_with_offset(body, x, y)
        actions.perform()
        time.sleep(0.5)

    def delete_cache(self):
        self.driver.execute_script("window.open('');")
        time.sleep(2)
        self.driver.switch_to.window(self.driver.window_handles[-1])
        time.sleep(2)
        self.driver.get("chrome://settings/clearBrowserData")  # for old chromedriver versions use cleardriverData
        time.sleep(2)
        actions = ActionChains(self.driver)
        actions.send_keys(Keys.TAB * 3 + Keys.DOWN * 3)  # send right combination
        actions.perform()
        time.sleep(2)
        actions = ActionChains(self.driver)
        actions.send_keys(Keys.TAB * 4 + Keys.ENTER)  # confirm
        actions.perform()
        time.sleep(5)  # wait some time to finish

    def reset(self):
        self.delete_cache()
        self.delete_all_cookies()
        time.sleep(3)

    @staticmethod
    def _generate_random_string():
        return "".join(random.choices(string.ascii_uppercase + string.digits, k=20))

    @staticmethod
    def get_proxy_username(self, option: ProxyOption) -> str:
        return f"groups-{option.group},session-{option.session},country-US"

    @property
    def page_source(self):
        return self.driver.page_source


class BaseLocalCrawler:
    def __init__(self, proxy: bool):
        self.proxy = proxy
        self.content_getter = None

    @abc.abstractmethod
    def start_crawler(self, task_ids: str, mbl_nos: str, booking_nos: str, container_nos: str):
        pass

    @staticmethod
    def get_response_selector(url, httptext, meta):
        return TextResponse(
            url=url,
            body=httptext,
            encoding="utf-8",
            request=Request(
                url=url,
                meta=meta,
            ),
        )

    def quit(self):
        self.content_getter.quit()

    def reset(self):
        self.content_getter.reset()
