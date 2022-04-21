import logging
import random
import string
import time

import scrapy
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.common.keys import Keys

from local.core import BaseLocalCrawler, BaseSeleniumContentGetter
from local.exceptions import AccessDeniedError, DataNotFoundError
from src.crawler.spiders.carrier_zimu import MainInfoRoutingRule

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
        except (TimeoutException, NoSuchElementException):
            pass

    def check_denied(self):
        response = scrapy.Selector(text=self.driver.page_source)

        alter_msg = response.xpath("/html/body/h1")
        if alter_msg:
            return True
        return False

    def randomize(self, random_count):
        probabilities = [
            0.3,  # typing
            0.1,  # mouse movement
            0.2,  # click
        ]

        if self.driver.current_url != "https://www.zim.com/tools/track-a-shipment":
            self.driver.get("https://www.zim.com/tools/track-a-shipment")

        for i in range(random_count):
            self.resting_mouse(end=[random.randint(10, 1900), random.randint(200, 1060)])
            if random.random() < probabilities[0]:
                search_bar = self.driver.find_element_by_css_selector("input[name='consnumber']")
                self.slow_type(search_bar, self.get_random_string())
                search_bar.send_keys(Keys.RETURN)
                time.sleep(2)
                search_bar = self.driver.find_element_by_css_selector("input[name='consnumber']")
                for _ in range(random.randint(6, 9)):
                    search_bar.send_keys(Keys.BACKSPACE)
                    time.sleep(float(random.uniform(0.05, 0.3)))

            if random.random() < probabilities[1]:
                self.resting_mouse(end=[random.randint(10, 1900), random.randint(200, 1060)])

            if random.random() < probabilities[2]:
                self.click_mouse()
                time.sleep(2)

            if self.driver.current_url != "https://www.zim.com/tools/track-a-shipment":
                self.driver.back()

    def search(self, mbl_no: str):
        self.driver.get("https://www.zim.com/tools/track-a-shipment")
        if self.check_denied():
            raise AccessDeniedError()

        self.randomize(random.randint(1, 3))
        self._accept_cookie()
        self.close_questionnaire()
        try:
            self.driver.find_element_by_xpath('//*[@id="popup_module"]/div/div/button/span').click()
        except NoSuchElementException:
            pass

        self.randomize(random.randint(1, 3))

        try:
            search_bar = self.driver.find_element_by_css_selector("input[name='consnumber']")
            self.action.move_to_element(search_bar).click().perform()
            self.slow_type(search_bar, mbl_no)
            search_bar.send_keys(Keys.RETURN)
            time.sleep(2)
        except (NoSuchElementException, StaleElementReferenceException):
            self.retry(mbl_no)

        self.close_questionnaire()

        try:
            self.driver.find_element_by_xpath('//*[@id="popup_module"]/div/div/button/span').click()
        except NoSuchElementException:
            pass

        return self.driver.page_source

    def get_random_string(self):
        return "".join(random.choice(string.ascii_uppercase + string.digits) for _ in range(random.randint(3, 5)))

    def close_questionnaire(self):
        try:
            self.driver.find_element_by_xpath('//*[@id="error-modal-newsletter-popup"]/div/div/button[1]').click()
        except:  # noqa: E722
            pass

    def retry(self, mbl_no: str):
        logger.info(f"retry {self.driver.current_url}")
        if self.driver.current_url != "chrome://welcome/":
            self.driver.back()
        if self.driver.current_url != "https://www.zim.com/tools/track-a-shipment":
            self.driver.get("https://www.zim.com/tools/track-a-shipment")

        if self.check_denied():
            raise AccessDeniedError()

        self.randomize(random.randint(1, 3))
        self._accept_cookie()
        self.close_questionnaire()

        if random.randint(1, 6) > 4:
            icon = self.driver.find_element_by_xpath("/html/body/div[4]/header/div[3]/div/div[1]/a/img")
            self.action.move_to_element(icon).click().perform()
            self.driver.back()
            self.randomize(random.randint(1, 3))

        if random.randint(1, 6) > 4:
            small_icon = self.driver.find_element_by_xpath(
                '//*[@id="main"]/div/div/div/div/div/div/div/div/div[1]/div/div[2]/button'
            )
            self.action.move_to_element(small_icon).click().perform()
            self.randomize(random.randint(1, 3))

        if random.randint(1, 6) > 4:
            contact_us = self.driver.find_element_by_xpath("/html/body/div[4]/header/div[2]/ul/li[1]/ul/li[2]/a")
            self.action.move_to_element(contact_us).click().perform()
            self.driver.back()
            self.scroll_down(wait=False)
            self.randomize(random.randint(1, 3))

        self.resting_mouse(end=[random.randint(1600, 1750), random.randint(400, 850)])
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

        if search_bar.get_attribute("value") != mbl_no:
            now_str = search_bar.get_attribute("value")
            for _ in range(random.randint(len(now_str), len(now_str) + 3)):
                search_bar.send_keys(Keys.BACKSPACE)
                time.sleep(float(random.uniform(0.05, 0.15)))
            self.slow_type(search_bar, mbl_no)

        self.close_questionnaire()
        search_bar.send_keys(Keys.RETURN)
        time.sleep(2)
        self.close_questionnaire()

    def search_and_return(self, mbl_no: str):
        # 10% chance to retry to increase chaos
        if random.random() < 0.1:
            self.retry(mbl_no)
        else:
            self.search(mbl_no=mbl_no)

        if self.check_denied():
            try:
                self.retry(mbl_no)
            finally:
                if self.check_denied():
                    raise AccessDeniedError()

        rnd = random.randint(1, 8)
        if rnd > 6:
            try:
                new_icon = self.driver.find_element_by_xpath(
                    '//*[@id="main"]/div/div/div/div/div/div/div/div/div[1]/div[2]/div[1]/div/dl[1]/dt[2]/a/span'
                )
                self.action.move_to_element(new_icon).click().perform()
            except NoSuchElementException:
                self.retry(mbl_no)
        elif rnd > 3:
            try:
                bus_icon = self.driver.find_element_by_xpath(
                    '//*[@id="main"]/div/div/div/div/div/div/div/div/div[1]/div[2]/div[1]/div/dl[2]/dd/a'
                )
                self.action.move_to_element(bus_icon).click().perform()
                windows = self.driver.window_handles
                if len(windows) > 1:
                    self.driver.switch_to.window(windows[1])
                    self.driver.close()
                    self.driver.switch_to.window(windows[0])
            except NoSuchElementException:
                self.retry(mbl_no)

        self.resting_mouse(end=[random.randint(1600, 1750), random.randint(400, 850)])
        self.scroll_down(wait=False)

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
