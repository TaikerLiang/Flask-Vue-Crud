import dataclasses
import random
import time
import string
import abc

from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from local.config import PROXY_URL, PROXY_PASSWORD


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

    def __init__(self):
        self.driver = None

    def go_to(self, url: str, seconds: int):
        self.driver.get(url=url)
        time.sleep(seconds)

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
        time.sleep(2)

    def back_to_previous(self):
        self.driver.back()
        time.sleep(2)

    def find_element_by_css_selector(self, css: str):
        return self.driver.find_element_by_css_selector(css_selector=css)

    def wait_for_appear(self, css: str, wait_sec: int):
        locator = (By.CSS_SELECTOR, css)
        WebDriverWait(self.driver, wait_sec).until(EC.presence_of_element_located(locator))

    def move_mouse_to_random_position(self):
        max_x, max_y = self.driver.execute_script("return [window.innerWidth, window.innerHeight];")
        body = self.driver.find_element_by_tag_name("body")
        actions = ActionChains(self.driver)
        x = random.randint(0, max_x)
        y = random.randint(0, max_y)
        # print("move_mouse_to_random_position", x, y)
        actions.move_to_element_with_offset(body, x, y)
        actions.perform()
        time.sleep(0.5)

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
    def __init__(self):
        self.content_getter = None

    @abc.abstractmethod
    def start_crawler(self, task_ids: str, mbl_nos: str, booking_nos: str, container_nos: str):
        pass

    def quit(self):
        self.content_getter.quit()
