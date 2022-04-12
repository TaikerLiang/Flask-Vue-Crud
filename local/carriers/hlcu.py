import time

from pyppeteer import logging
from scrapy.selector import Selector
from selenium.common.exceptions import ElementNotInteractableException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from local.core import BaseLocalCrawler, BaseSeleniumContentGetter
from src.crawler.core_carrier.exceptions import (
    CARRIER_RESULT_STATUS_ERROR,
    LoadWebsiteTimeOutError,
)
from src.crawler.core_carrier.items import ContainerItem, ExportErrorData
from src.crawler.spiders.carrier_hlcu_multi import TracingRoutingRule

BASE_URL = "https://www.hapag-lloyd.com/en"
SEARCH_URL = f"{BASE_URL}/online-business/track/track-by-booking-solution.html"

MAX_RETRY_COUNT = 1


class HlcuContentGetter(BaseSeleniumContentGetter):
    def __init__(self, proxy: bool):
        super().__init__(proxy=proxy)
        logging.disable(logging.DEBUG)
        self.retry_count = 0

    def connect(self):
        self.driver.get(SEARCH_URL)
        time.sleep(5)

    def restart(self):
        if self.retry_count >= MAX_RETRY_COUNT:
            raise LoadWebsiteTimeOutError(url=self.driver.current_url)

        self.retry_count += 1
        self.driver.close()

        super().__init__(proxy=self.proxy)
        self.connect()

    def get_mbl_page(self, mbl_no: str, need_handle_popup: bool = False):
        self.driver.get(f"{SEARCH_URL}?blno={mbl_no}")

        if need_handle_popup:
            try:
                self._confirm_privacy_choices()
            except TimeoutException:
                self.restart()
                self.get_mbl_page(mbl_no, need_handle_popup)

        return self.driver.page_source

    def get_container_page(self, index):
        self.driver.find_elements(By.CSS_SELECTOR, "div.hl-radio")[index].click()
        self.driver.find_elements(By.CSS_SELECTOR, "button[value='Details']")[0].click()
        page_source = self.driver.page_source
        return page_source

    def _confirm_privacy_choices(self):
        confirm_button_css = "button.save-preference-btn-handler.onetrust-close-btn-handler"

        WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, confirm_button_css)))
        button = self.driver.find_element(By.CSS_SELECTOR, confirm_button_css)
        try:
            button.click()
        except ElementNotInteractableException:
            pass


class HlcuLocalCrawler(BaseLocalCrawler):
    code = "HLCU"

    def __init__(self, proxy: bool):
        super().__init__(proxy=proxy)
        self._search_type = ""
        self._search_nos = []
        self.content_getter = HlcuContentGetter(proxy=proxy)
        self.rule = TracingRoutingRule(content_getter=None)

    def start_crawler(self, task_ids: str, mbl_nos: str, booking_nos: str, container_nos: str):
        task_ids = task_ids.split(",")
        mbl_nos = mbl_nos.split(",")
        id_mbl_map = {mbl_no: task_id for task_id, mbl_no in zip(task_ids, mbl_nos)}

        for mbl_no, task_id in id_mbl_map.items():
            mbl_page = self.content_getter.get_mbl_page(mbl_no=mbl_no, need_handle_popup=True)
            selector = Selector(text=mbl_page)
            for item in self.handle_mbl_page(selector, mbl_no, task_id):
                yield item

    def handle_mbl_page(self, selector: Selector, mbl_no, task_id):
        if self.rule._is_mbl_no_invalid(selector):
            yield ExportErrorData(
                mbl_no=mbl_no,
                task_id=task_id,
                status=CARRIER_RESULT_STATUS_ERROR,
                detail="Data was not found",
            )
            return

        container_nos = self.rule._extract_container_nos(response=selector)
        if not container_nos:
            yield ExportErrorData(
                mbl_no=mbl_no,
                task_id=task_id,
                status=CARRIER_RESULT_STATUS_ERROR,
                detail="Data was not found",
            )
            return

        for index, container_no in enumerate(container_nos):
            yield ContainerItem(
                task_id=task_id,
                container_no=container_no,
                container_key=container_no,
            )

            self.content_getter.get_mbl_page(mbl_no=mbl_no)
            container_page = self.content_getter.get_container_page(index=index)
            for status_item in self.rule._handle_container(
                page=container_page, container_no=container_no, task_id=task_id
            ):
                yield status_item
