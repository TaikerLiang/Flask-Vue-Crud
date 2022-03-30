import logging
import random
import time

import scrapy
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.keys import Keys

from local.core import BaseLocalCrawler, BaseSeleniumContentGetter
from local.exceptions import AccessDeniedError, DataNotFoundError
from local.proxy import HydraproxyProxyManager, ProxyManager
from src.crawler.spiders.carrier_zimu import MainInfoRoutingRule

logger = logging.getLogger("local-crawler-zimu")


class ZimuContentGetter(BaseSeleniumContentGetter):
    def __init__(self, proxy_manager: ProxyManager = None):
        super().__init__(proxy_manager)
        self._is_first = True

    def _accept_cookie(self):
        accept_btn_css = "#onetrust-accept-btn-handler"
        try:
            cookie_btn = self.driver.find_element_by_css_selector(accept_btn_css)
            cookie_btn.click()
            time.sleep(3)
        except (TimeoutException, NoSuchElementException):
            pass

    def search_and_return(self, mbl_no: str):
        self.driver.get("https://api.myip.com/")
        time.sleep(5)
        self.driver.get("https://www.zim.com/tools/track-a-shipment")

        self._accept_cookie()

        for i in range(random.randint(1, 3)):
            self.move_mouse_to_random_position()

        search_bar = self.driver.find_element_by_css_selector("input[name='consnumber']")
        self.action.move_to_element(search_bar).click().perform()
        time.sleep(2)
        search_bar.send_keys(mbl_no)
        time.sleep(2)
        search_bar.send_keys(Keys.RETURN)
        time.sleep(10)
        self.scroll_down()

        return self.driver.page_source


class ZimuLocalCrawler(BaseLocalCrawler):
    code = "ZIMU"

    def __init__(self):
        super().__init__()
        self.content_getter = ZimuContentGetter(proxy_manager=HydraproxyProxyManager(logger=logger))

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
                if not item:
                    return
                yield item

    @staticmethod
    def _is_mbl_no_invalid(response) -> bool:
        no_result_information = response.css("section#noResult p")
        if no_result_information:
            return True
