from typing import Optional
import dataclasses
import random
import string
import logging
import time

import scrapy
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, TimeoutException

from local.core import BaseLocalCrawler
from local.exceptions import AccessDeniedError, DataNotFoundError
from src.crawler.core_carrier.exceptions import LoadWebsiteTimeOutError
from src.crawler.core.pyppeteer import PyppeteerContentGetter
from local.core import BaseSeleniumContentGetter
from src.crawler.spiders.carrier_zimu import MainInfoRoutingRule


@dataclasses.dataclass
class ProxyOption:
    group: str
    session: str


logger = logging.getLogger("local-crawler-zimu")


class ZimuContentGetter(BaseSeleniumContentGetter):
    def __init__(self, proxy: bool):
        super().__init__(proxy=proxy)
        self._is_first = True

    def _accept_cookie(self):
        accept_btn_css = "#onetrust-accept-btn-handler"
        try:
            cookie_btn = self.driver.find_element_by_css_selector(accept_btn_css)
            cookie_btn.click()
            time.sleep(3)
        except (TimeoutException, NoSuchElementException):
            pass

    def check_denied(self, res):
        response = scrapy.Selector(text=res)

        alter_msg = response.xpath("/html/body/h1")
        if alter_msg:
            return True
        return False

    def search(self, mbl_no: str):
        self.driver.get("https://api.myip.com/")
        time.sleep(3)
        self.driver.get("https://www.zim.com/tools/track-a-shipment")
        if self.proxy:
            time.sleep(20)
        else:
            time.sleep(5)

        self._accept_cookie()

        for i in range(random.randint(1, 3)):
            self.move_mouse_to_random_position()
        if not self.proxy:
            if random.randint(1, 6) > 3:
                icon = self.driver.find_element_by_xpath("/html/body/div[4]/header/div[3]/div/div[1]/a/img")
                self.action.move_to_element(icon).click().perform()
                time.sleep(2)
                self.driver.back()
                time.sleep(5)

        search_bar = self.driver.find_element_by_css_selector("input[name='consnumber']")
        self.action.move_to_element(search_bar).click().perform()
        self.slow_type(search_bar, mbl_no)
        search_bar.send_keys(Keys.RETURN)
        if self.proxy:
            time.sleep(16)
        else:
            time.sleep(7)

        return self.driver.page_source

    def get_random_string(self):
        return "".join(random.choice(string.ascii_uppercase + string.digits) for _ in range(5))

    def retry(self, mbl_no: str):
        self.driver.back()
        time.sleep(2)
        for i in range(random.randint(1, 3)):
            self.move_mouse_to_random_position()

        if random.randint(1, 6) > 4:
            icon = self.driver.find_element_by_xpath("/html/body/div[4]/header/div[3]/div/div[1]/a/img")
            self.action.move_to_element(icon).click().perform()
            time.sleep(2)
            self.driver.back()
            time.sleep(5)

        if random.randint(1, 6) > 4:
            small_icon = self.driver.find_element_by_xpath(
                '//*[@id="main"]/div/div/div/div/div/div/div/div/div[1]/div/div[2]/button'
            )
            self.action.move_to_element(small_icon).click().perform()
            time.sleep(5)

        if random.randint(1, 6) > 4:
            contact_us = self.driver.find_element_by_xpath("/html/body/div[4]/header/div[2]/ul/li[1]/ul/li[2]/a")
            self.action.move_to_element(contact_us).click().perform()
            time.sleep(5)
            self.driver.back()
            time.sleep(5)
            self.scroll_down()

        self.resting_mouse()
        search_bar = self.driver.find_element_by_css_selector("input[name='consnumber']")

        if random.randint(1, 6) > 4:
            for _ in range(random.randint(15, 20)):
                search_bar.send_keys(Keys.BACKSPACE)
                time.sleep(float(random.uniform(0.05, 0.15)))
            self.slow_type(search_bar, self.get_random_string())
            search_bar.send_keys(Keys.RETURN)
            time.sleep(2)
            for _ in range(random.randint(6, 9)):
                search_bar.send_keys(Keys.BACKSPACE)
                time.sleep(float(random.uniform(0.05, 0.3)))
            self.slow_type(search_bar, mbl_no)

        search_bar.send_keys(Keys.RETURN)
        time.sleep(5)

    def search_and_return(self, mbl_no: str):
        if self.check_denied(self.search(mbl_no=mbl_no)) and not self.proxy:
            self.retry(mbl_no)
        elif self.proxy:
            pass
        else:
            rnd = random.randint(1, 8)
            if rnd > 6:
                new_icon = self.driver.find_element_by_xpath(
                    '//*[@id="main"]/div/div/div/div/div/div/div/div/div[1]/div[2]/div[1]/div/dl[1]/dt[2]/a/span'
                )
                self.action.move_to_element(new_icon).click().perform()
                time.sleep(2)
            elif rnd > 3:
                bus_icon = self.driver.find_element_by_xpath(
                    '//*[@id="main"]/div/div/div/div/div/div/div/div/div[1]/div[2]/div[1]/div/dl[2]/dd/a'
                )
                self.action.move_to_element(bus_icon).click().perform()
                time.sleep(3)
                windows = self.driver.window_handles
                if len(windows) > 1:
                    self.driver.switch_to.window(windows[1])
                    self.driver.close()
                    self.driver.switch_to.window(windows[0])

            self.resting_mouse()
            time.sleep(1)
            self.scroll_down()

        return self.driver.page_source


class ZimuLocalCrawler(BaseLocalCrawler):
    code = "ZIMU"

    def __init__(self, proxy: bool):
        super().__init__(proxy=proxy)
        self.content_getter = ZimuContentGetter(proxy=proxy)

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
