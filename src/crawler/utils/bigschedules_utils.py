from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
import os

from crawler.core_carrier.exceptions import LoadWebsiteTimeOutError

PATH = os.path.dirname(os.path.abspath(__file__))

# CHROME_DRIVER_PATH = '%s/chromedriver' % PATH

browser = None


def init_browser():
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-extensions")
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")
    global browser
    browser = webdriver.Chrome(chrome_options=options)
    browser.get('https://www.bigschedules.com')

    try:
        WebDriverWait(browser, 5).until(expected_conditions.visibility_of_element_located((By.XPATH, "//button[@class='csck-btn csck-btn-solid']")))
    except TimeoutException as e:
        raise LoadWebsiteTimeOutError()

    # allow cookies usage
    buttons = browser.find_elements_by_xpath("//button[@class='csck-btn csck-btn-solid']")
    buttons[0].click()

    click_search_button()


def click_search_button():
    try:
        WebDriverWait(browser, 10).until(
            expected_conditions.visibility_of_element_located((By.XPATH, "//span[@id='main_feature_beta_span_close']")))
    except TimeoutException as e:
        raise LoadWebsiteTimeOutError()

    close_button = browser.find_element_by_xpath("//span[@id='main_feature_beta_span_close']")
    close_button.click()

    try:
        WebDriverWait(browser, 5).until(
            expected_conditions.visibility_of_element_located((By.XPATH, "//a[@id='main_a_search']")))
    except TimeoutException as e:
        raise LoadWebsiteTimeOutError()

    search_button = browser.find_element_by_xpath("//a[@id='main_a_search']")
    search_button.click()


def get_user_detect_cookie():
    if browser is None:
        init_browser()

    user_detect_cookie = {}

    for cookie in browser.get_cookies():
        if cookie['name'] == 'USER_BEHAVIOR_DETECT':
            user_detect_cookie[cookie['name']] = cookie['value']
            break

    return user_detect_cookie
