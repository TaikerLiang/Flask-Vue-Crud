from typing import List
import time
import random


from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from local.core import BaseContentGetter, BaseLocalCrawler


class TrapacContentGetter(BaseContentGetter):
    UPPER_SHORT = ""
    LOWER_SHORT = ""
    EMAIL = ""
    PASSWORD = ""

    def __init__(self):
        super().__init__()
        options = webdriver.ChromeOptions()
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-notifications")
        # options.add_argument("--headless")
        options.add_argument("--enable-javascript")
        options.add_argument("window-size=1920,1080")
        options.add_argument(
            f"user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 11_1_0) AppleWebKit/537.36 (KHTML, like Gecko) "
            f"Chrome/88.0.4324.96 Safari/537.36"
        )
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        self.driver = webdriver.Chrome(chrome_options=options)

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
