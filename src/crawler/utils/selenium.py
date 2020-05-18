from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait

from crawler.core_vessel.exceptions import LoadWebsiteTimeOutError


class BaseChromeDriver:

    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--disable-extensions")
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--window-size=1920,1080")

        self._browser = webdriver.Chrome(chrome_options=options)

    def _click_button(self, xpath: str, wait_time: int):
        try:
            WebDriverWait(self._browser, wait_time).until(expected_conditions.visibility_of_element_located(
                (By.XPATH, xpath)))
        except TimeoutException as e:
            raise LoadWebsiteTimeOutError()

        button = self._browser.find_element_by_xpath(xpath=xpath)
        button.click()
