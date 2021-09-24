from selenium import webdriver
import random


class BaseContentGetter:
    def __init__(self):
        self._driver = None

    def get_current_url(self):
        return self._driver.current_url

    def scroll_to_bottom_of_page(self):
        self.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    def get_page_source(self):
        return self._driver.page_source

    def get_cookies(self):
        return self._driver.get_cookies()

    def execute_script(self, script: str):
        self._driver.execute_script(script)

    def quit(self):
        self._driver.quit()

    def page_refresh(self):
        self._driver.refresh()

    def close(self):
        self._driver.close()

    def check_alert(self):
        alert = self._driver.switch_to.alert
        text = alert.text


class ChromeContentGetter(BaseContentGetter):
    def __init__(self):
        super().__init__()

        options = webdriver.ChromeOptions()
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-notifications")
        options.add_argument("--headless")
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

        self._driver = webdriver.Chrome(chrome_options=options)


class FirefoxContentGetter(BaseContentGetter):
    def __init__(self, service_log_path=None):
        super().__init__()

        useragent = self._random_choose_user_agent()
        profile = webdriver.FirefoxProfile()
        profile.set_preference("general.useragent.override", useragent)
        options = webdriver.FirefoxOptions()
        options.set_preference("dom.webnotifications.serviceworker.enabled", False)
        options.set_preference("dom.webnotifications.enabled", False)
        options.add_argument("--headless")

        self._driver = webdriver.Firefox(firefox_profile=profile, options=options, service_log_path=service_log_path)

    @staticmethod
    def _random_choose_user_agent():
        user_agents = [
            # firefox
            ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:80.0) " "Gecko/20100101 " "Firefox/80.0"),
            ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:79.0) " "Gecko/20100101 " "Firefox/79.0"),
            ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:78.0) " "Gecko/20100101 " "Firefox/78.0"),
            ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:78.0.1) " "Gecko/20100101 " "Firefox/78.0.1"),
        ]

        return random.choice(user_agents)
