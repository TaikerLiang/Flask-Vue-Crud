from typing import List
import time
import random


from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from local.core import BaseSeleniumContentGetter


class TrapacContentGetter(BaseSeleniumContentGetter):
    UPPER_SHORT = ""
    LOWER_SHORT = ""
    EMAIL = ""
    PASSWORD = ""

    def __init__(self):
        super().__init__(proxy_manager=None)

    def search_and_return(self, container_no_list: List):
        self.go_to(
            url=f"https://{self.LOWER_SHORT}.trapac.com/quick-check/?terminal={self.UPPER_SHORT}&transaction=availability",
            seconds=10,
        )
        # self.accept_cookie()
        self.key_in_search_bar(search_no=",".join(container_no_list))
        self.press_search_button()

        return self.get_result_response_text()

    def accept_cookie(self):
        try:
            cookie_btn = self.driver.find_element_by_xpath('//*[@id="cn-accept-cookie"]')
            cookie_btn.click()
            time.sleep(3)
        except NoSuchElementException:
            pass

    def key_in_search_bar(self, search_no: str):
        text_area = self.driver.find_element_by_xpath('//*[@id="edit-containers"]')
        text_area.send_keys(search_no)
        time.sleep(3)

    def press_search_button(self):
        search_btn = self.driver.find_element_by_xpath('//*[@id="transaction-form"]/div[3]/button')
        search_btn.click()
        time.sleep(10)

    def get_result_response_text(self):
        result_table_css = "div#transaction-detail-result table"
        self.wait_for_appear(css=result_table_css, wait_sec=20)
        return self.page_source

    def get_google_recaptcha(self):
        return self.driver.find_element_by_xpath('//*[@id="recaptcha-backup"]')
