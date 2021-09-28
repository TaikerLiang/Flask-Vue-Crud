import re
import io
import base64
import json
import time

import scrapy
import PIL.Image as Image
from python_anticaptcha import AnticaptchaClient, ImageToTextTask, AnticaptchaException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from crawler.core_air.items import (
    BaseAirItem,
    AirItem,
    DebugItem,
    ExportErrorData,
    HistoryItem,
)
from crawler.core_air.base import AIR_RESULT_STATUS_ERROR, AIR_RESULT_STATUS_FATAL
from crawler.core_air.base_spiders import BaseMultiAirSpider
from crawler.core_air.exceptions import AntiCaptchaError
from crawler.core_air.request_helpers import RequestOption
from crawler.core_air.rules import RuleManager, BaseRoutingRule
from crawler.core.selenium import FirefoxContentGetter

PREFIX = '112'
CAPTCHA_RETRY_LIMIT = 5


class AirChinaEasternSpider(BaseMultiAirSpider):
    name = 'air_china_eastern'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        rules = [
            AirInfoRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)

    def start(self):
        driver = ContentGetter()
        try:
            driver.handle_cookie()
            token = driver.handle_captcha()
            driver.close()
        except AntiCaptchaError:
            yield ExportErrorData(status=AIR_RESULT_STATUS_FATAL, detail=f'<anti-captcha-error>')
            driver.close()
            return

        for mawb_no, task_id in zip(self.mawb_nos, self.task_ids):
            option = AirInfoRoutingRule.build_request_option(mawb_no=mawb_no, task_id=task_id, token=token)
            yield self._build_request_by(option=option)

    def parse(self, response):
        yield DebugItem(info={'meta': dict(response.meta)})

        routing_rule = self._rule_manager.get_rule_by_response(response=response)
        save_name = routing_rule.get_save_name(response=response)
        self._saver.save(to=save_name, text=response.text)

        for result in routing_rule.handle(response=response):
            if isinstance(result, BaseAirItem):
                yield result
            elif isinstance(result, RequestOption):
                yield self._build_request_by(option=result)
            else:
                raise RuntimeError()

    def _build_request_by(self, option: RequestOption):
        meta = {
            RuleManager.META_AIR_CORE_RULE_NAME: option.rule_name,
            **option.meta,
        }

        if option.method == RequestOption.METHOD_POST_BODY:
            return scrapy.Request(
                method='POST',
                url=option.url,
                headers=option.headers,
                body=option.body,
                meta=meta,
                dont_filter=True,
            )
        elif option.method == RequestOption.METHOD_GET:
            return scrapy.Request(
                url=option.url,
                meta=meta,
                headers=option.headers,
            )
        else:
            raise ValueError(f"Invalid option.method [{option.method}]")


class AirInfoRoutingRule(BaseRoutingRule):
    name = 'AIR_INFO'

    @classmethod
    def build_request_option(cls, mawb_no: str, task_id: str, token: str) -> RequestOption:
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=(
                f'https://www.skyteam.com/api/skyLinkApi?Type=ctt&path=cargo/v2&awb={PREFIX}-{mawb_no}'
                f'&Token={token}&lang=en'
            ),
            headers=({
                'authority': 'www.skyteam.com',
                'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36',
                'referer': 'https://www.skyteam.com/en/cargo/track-shipment/',
                'accept-language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            }),
            meta={
                    'mawb_no': mawb_no,
                    'task_id': task_id,
                }
        )

    def get_save_name(self, response) -> str:
        return f'{self.name} {response.meta["mawb_no"]}.json'

    def handle(self, response):
        mawb_no = response.meta['mawb_no']
        task_id = response.meta['task_id']
        response_dict = json.loads(response.text)
        if self.is_mawb_no_invalid(response_dict):
            yield ExportErrorData(status=AIR_RESULT_STATUS_ERROR, detail="Data was not found")
            return
        air_info = self.extract_air_info(response_dict)
        yield AirItem(task_id=task_id, mawb=mawb_no, **air_info)
        history_list = self.extract_history_info(response_dict)
        for history in history_list:
            yield HistoryItem(task_id=task_id, **history)

    def is_mawb_no_invalid(self, response):
        if "ErrorMessage" in response:
            return True
        return False

    def extract_air_info(self, response):
        current_state = response["Segments"]["Segment"][-1]["StatusCode"]
        return {
            'pieces': response["NumberOfPieces"],
            'weight': response["Weight"],
            'origin': response["Origin"],
            'destination': response["Destination"],
            'current_state': current_state,
        }

    def extract_history_info(self, response):
        history_list = []
        for event in response['Segments']['Segment']:
            history_list.append(
                {
                    'status': event['StatusDescription'],
                    'pieces': event['NumberOfPieces'],
                    'weight': event['Weight'],
                    'time': f"{event['EventDate']} {event['EventTime']}",
                    'location': event['EventLocation'],
                    'flight_number': event['FlightNumber'],
                }
            )
        return history_list


class ContentGetter(FirefoxContentGetter):
    def handle_cookie(self):
        self._driver.get('https://www.skyteam.com/en/cargo/track-shipment/')
        cookie_btn = WebDriverWait(self._driver, 30).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'a.cb-enable'))
        )
        cookie_btn.click()

    def handle_captcha(self):
        WebDriverWait(self._driver, 30).until(
            EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, "iframe#mtcaptcha-iframe-1")))
        for i in range(CAPTCHA_RETRY_LIMIT):
            captcha_text = self._solve_captcha()
            search_bar = self._driver.find_element_by_css_selector('input#mtcap-inputtext-1')
            search_bar.send_keys(captcha_text)
            time.sleep(3)
            solve_text = self._driver.find_element_by_css_selector('span.mtcap-hidden-aria').text
            if solve_text == "captcha verified successfully.":
                self._driver.switch_to.default_content()
                token = self._driver.find_element_by_css_selector('input.mtcaptcha-verifiedtoken').get_attribute('value')
                return token
        self._driver.switch_to.default_content()
        raise AntiCaptchaError()

    def _solve_captcha(self):
        response = scrapy.Selector(text=self.get_page_source())
        src = response.css('img.mtcap-show-if-nocss::attr(src)').get()
        pattern = re.compile(r'data:image/png;base64,(?P<base64>.+)$')
        base64_match = pattern.match(src)
        if base64_match:
            base64 = base64_match.group('base64')
            file_name = 'captcha.png'
            image = self._readb64(base64)
            image.save(file_name)
        else:
            return ''

        try:
            api_key = 'fbe73f747afc996b624e8d2a95fa0f84'
            captcha_fp = open('captcha.png', 'rb')
            client = AnticaptchaClient(api_key)
            task = ImageToTextTask(captcha_fp)
            job = client.createTask(task)
            job.join()
            captcha_text = job.get_captcha_text()
            return captcha_text
        except AnticaptchaException:
            raise AntiCaptchaError()

    def _readb64(self, base64_string):
        _imgdata = base64.b64decode(base64_string)
        image = Image.open(io.BytesIO(_imgdata))

        return image

    def scroll_page_down(self):
        body = self._driver.find_element_by_xpath('/html/body')
        body.send_keys(Keys.PAGE_DOWN)
        time.sleep(0.5)

