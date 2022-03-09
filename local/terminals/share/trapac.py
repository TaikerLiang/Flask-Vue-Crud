import time
from typing import List

from local.core import BaseSeleniumContentGetter


class TrapacContentGetter(BaseSeleniumContentGetter):
    UPPER_SHORT = ""
    LOWER_SHORT = ""
    EMAIL = ""
    PASSWORD = ""

    def __init__(self, proxy: bool):
        super().__init__(proxy=proxy)

    def search_and_return(self, container_no_list: List):
        self.go_to(
            url="https://www.trapac.com/",
            seconds=10,
        )
        self.accept_cookie()

        if self.UPPER_SHORT == 'LAX':
            link = self.driver.find_element_by_xpath('/html/body/div[1]/div/div/div[1]/ul/li[2]/a')
        elif self.UPPER_SHORT == 'OAK':
            link = self.driver.find_element_by_xpath('/html/body/div[1]/div/div/div[1]/ul/li[3]/a')
        else:
            link = self.driver.find_element_by_xpath('/html/body/div[1]/div/div/div[1]/ul/li[4]/a')

        self.action.move_to_element(link).click().perform()
        time.sleep(10)

        if self.UPPER_SHORT == 'LAX':
            menu = self.driver.find_element_by_xpath('//*[@id="menu-item-74"]/a')
        elif self.UPPER_SHORT == 'OAK':
            menu = self.driver.find_element_by_xpath('//*[@id="menu-item-245"]/a')
        else:
            menu = self.driver.find_element_by_xpath('//*[@id="menu-item-248"]/a')

        self.action.move_to_element(menu).click().perform()
        time.sleep(3)
        self.go_to(
            url=f"https://{self.LOWER_SHORT}.trapac.com/quick-check/?terminal={self.UPPER_SHORT}&transaction=availability",
            seconds=15,
        )
        self.go_to(
            url=f"https://{self.LOWER_SHORT}.trapac.com/quick-check/?terminal={self.UPPER_SHORT}&transaction=availability",
            seconds=15,
        )
        # # self.scroll_up()
        # self.move_mouse_to_random_position()
        self.human_action()
        time.sleep(3)
        self.key_in_search_bar(search_no="\n".join(container_no_list))
        self.press_search_button()
        self.accept_cookie()

        return self.get_result_response_text()

    def accept_cookie(self):
        try:
            cookie_btn = self.driver.find_element_by_xpath('//*[@id="cn-accept-cookie"]')
            self.action.move_to_element(cookie_btn).click().perform()
            time.sleep(3)
        except:
            pass

    def human_action(self):
        try:
            self.driver.find_element_by_xpath('//*[@id="transaction-form"]/div[1]/fieldset[1]/ul/li[2]/label').click()
            time.sleep(1)
            self.driver.find_element_by_xpath('//*[@id="transaction-form"]/div[1]/fieldset[1]/ul/li[1]/label').click()
            time.sleep(1)
            self.driver.find_element_by_xpath('//*[@id="transaction-form"]/div[1]/fieldset[1]/ul/li[3]/label').click()
            time.sleep(1)
        except:
            pass

        if self.UPPER_SHORT == 'LAX':
            self.driver.find_element_by_xpath('//*[@id="transaction-form"]/div[1]/fieldset[1]/ul/li[1]/label').click()
            time.sleep(1)
        elif self.UPPER_SHORT == 'OAK':
            self.driver.find_element_by_xpath('//*[@id="transaction-form"]/div[1]/fieldset[1]/ul/li[2]/label').click()
            time.sleep(1)
        else:
            self.driver.find_element_by_xpath('//*[@id="transaction-form"]/div[1]/fieldset[1]/ul/li[3]/label').click()
            time.sleep(1)

    def key_in_search_bar(self, search_no: str):
        textarea = self.driver.find_element_by_xpath('//*[@id="edit-containers"]')
        self.action.move_to_element(textarea).click().perform()
        self.slow_type(textarea, search_no)
        time.sleep(3)

    def press_search_button(self):
        search_btn = self.driver.find_element_by_xpath('//*[@id="transaction-form"]/div[3]/button')
        self.action.move_to_element(search_btn).click().perform()
        time.sleep(90)
        self.scroll_down()
        self.scroll_up()

    def get_result_response_text(self):
        result_table_css = "div#transaction-detail-result table"
        self.wait_for_appear(css=result_table_css, wait_sec=20)
        return self.page_source

    def get_google_recaptcha(self):
        return self.driver.find_element_by_xpath('//*[@id="recaptcha-backup"]')
