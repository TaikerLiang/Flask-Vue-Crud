import dataclasses
import time
import random

import scrapy
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import TimeoutException
from urllib3.exceptions import ReadTimeoutError

from local.core import BaseContentGetter, BaseLocalCrawler
from local.exceptions import AccessDeniedError, DataNotFoundError
from src.crawler.core_carrier.exceptions import LoadWebsiteTimeOutError
from src.crawler.spiders.carrier_zimu import MainInfoRoutingRule


@dataclasses.dataclass
class ProxyOption:
    group: str
    session: str


class ZimuContentGetter(BaseContentGetter):
    def __init__(self):
        super().__init__()
        options = webdriver.ChromeOptions()
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-infobars")
        # options.add_argument('--headless')
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

        prefs = {"profile.managed_default_content_settings.images": 2}
        options.add_experimental_option("prefs", prefs)

        self.driver = webdriver.Chrome(chrome_options=options)
        self._is_first = True

    def _accept_cookie(self):
        try:
            accept_btn = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="onetrust-accept-btn-handler"]'))
            )
        except (TimeoutException, ReadTimeoutError):
            raise LoadWebsiteTimeOutError(url="https://www.zim.com/tools/track-a-shipment")

        time.sleep(1)
        accept_btn.click()

    def search_and_return(self, mbl_no: str):
        # create action chain object
        action = ActionChains(self.driver)

        self.driver.set_page_load_timeout(30)
        self.driver.get("https://www.zim.com/tools/track-a-shipment")

        if self._is_first:
            self._is_first = False
            self._accept_cookie()
            location = self.driver.find_element(By.CSS_SELECTOR, "a.location")
            action.move_to_element(location).perform()

        search_bar = self.driver.find_elements_by_css_selector("input[name='consnumber']")[0]
        search_btn = self.driver.find_elements_by_css_selector("input[value='Track Shipment']")[0]

        for i in range(random.randint(1, 3)):
            self.move_mouse_to_random_position()

        action.move_to_element(search_bar).click().perform()
        time.sleep(2)
        search_bar.send_keys(mbl_no)
        time.sleep(2)
        search_bar.send_keys(Keys.ENTER)
        time.sleep(20)
        self.scroll_down()

        return self.driver.page_source


class ZimuLocalCrawler(BaseLocalCrawler):
    code = "ZIMU"

    def __init__(self):
        super().__init__()
        self.content_getter = ZimuContentGetter()

    def start_crawler(self, task_ids: str, mbl_nos: str, booking_nos: str, container_nos: str):
        task_ids = task_ids.split(",")
        mbl_nos = mbl_nos.split(",")
        id_mbl_map = {mbl_no: task_id for task_id, mbl_no in zip(task_ids, mbl_nos)}

        for mbl_no, task_id in id_mbl_map.items():
            yield {"task_id": task_id}
            res = self.content_getter.search_and_return(mbl_no=mbl_no)
            response = scrapy.Selector(text=res)

            alter_msg = response.xpath("/html/body/h1")
            if alter_msg:
                print("alter_msg.extract()", alter_msg.extract())
                raise AccessDeniedError()

            if self._is_mbl_no_invalid(response=response):
                raise DataNotFoundError(task_id=task_id)

            main_rule = MainInfoRoutingRule()
            main_rule.handle_item(response=response)

            for item in main_rule.handle_item(response=response):
                yield item

    @staticmethod
    def _is_mbl_no_invalid(response) -> bool:
        no_result_information = response.css("section#noResult p")
        if no_result_information:
            return True
