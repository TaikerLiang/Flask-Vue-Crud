import base64
import json
import re
import time

import scrapy
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from crawler.core.base import RESULT_STATUS_ERROR, SEARCH_TYPE_AWB
from crawler.core.exceptions import GeneralFatalError, SuspiciousOperationError
from crawler.core.items import DataNotFoundItem
from crawler.core.selenium import FirefoxContentGetter
from crawler.core_air.base_spiders import BaseMultiAirSpider
from crawler.core_air.items import AirItem, BaseAirItem, DebugItem, HistoryItem
from crawler.core_air.request_helpers import RequestOption
from crawler.core_air.rules import BaseRoutingRule, RuleManager
from crawler.services.captcha_service import ImageAntiCaptchaService

PREFIX = "112"
CAPTCHA_RETRY_LIMIT = 5


class AirChinaEasternSpider(BaseMultiAirSpider):
    name = "air_china_eastern"

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
        except GeneralFatalError as e:
            yield e
            driver.close()
            return

        for mawb_no, task_id in zip(self.mawb_nos, self.task_ids):
            option = AirInfoRoutingRule.build_request_option(mawb_no=mawb_no, task_id=task_id, token=token)
            yield self._build_request_by(option=option)

    def parse(self, response):
        yield DebugItem(info={"meta": dict(response.meta)})

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
                method="POST",
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
            map_dict = {option.meta["search_no"]: self.mno_tid_map[option.meta["search_no"]]}
            raise SuspiciousOperationError(
                task_id=self.mno_tid_map[option.meta["search_no"]][0],
                search_no=option.meta["search_no"],
                search_type=self.search_type,
                reason=f"Unexpected request method: `{option.method}`, on (search_no: [task_id...]): {map_dict}",
            )


class AirInfoRoutingRule(BaseRoutingRule):
    name = "AIR_INFO"

    @classmethod
    def build_request_option(cls, mawb_no: str, task_id: str, token: str) -> RequestOption:
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=(
                f"https://www.skyteam.com/api/skyLinkApi?Type=ctt&path=cargo/v2&awb={PREFIX}-{mawb_no}"
                f"&Token={token}&lang=en"
            ),
            headers=(
                {
                    "authority": "www.skyteam.com",
                    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36",
                    "referer": "https://www.skyteam.com/en/cargo/track-shipment/",
                    "accept-language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
                }
            ),
            meta={
                "search_no": mawb_no,
                "task_id": task_id,
            },
        )

    def get_save_name(self, response) -> str:
        return f'{self.name} {response.meta["search_no"]}.json'

    def handle(self, response):
        mawb_no = response.meta["search_no"]
        task_id = response.meta["task_id"]
        response_dict = json.loads(response.text)
        if self.is_mawb_no_invalid(response_dict):
            yield DataNotFoundItem(
                status=RESULT_STATUS_ERROR,
                detail="Data was not found",
                task_id=task_id,
                search_no=mawb_no,
                search_type=SEARCH_TYPE_AWB,
            )
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
            "pieces": response["NumberOfPieces"],
            "weight": response["Weight"],
            "origin": response["Origin"],
            "destination": response["Destination"],
            "current_state": current_state,
        }

    def extract_history_info(self, response):
        history_list = []
        for event in response["Segments"]["Segment"]:
            history_list.append(
                {
                    "status": event["StatusDescription"],
                    "pieces": event["NumberOfPieces"],
                    "weight": event["Weight"],
                    "time": f"{event['EventDate']} {event['EventTime']}",
                    "location": event["EventLocation"],
                    "flight_number": event["FlightNumber"],
                }
            )
        return history_list


class ContentGetter(FirefoxContentGetter):
    def handle_cookie(self):
        self._driver.get("https://www.skyteam.com/en/cargo/track-shipment/")
        cookie_btn = WebDriverWait(self._driver, 30).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a.cb-enable")))
        cookie_btn.click()

    def handle_captcha(self):
        WebDriverWait(self._driver, 30).until(
            EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, "iframe#mtcaptcha-iframe-1"))
        )
        for i in range(CAPTCHA_RETRY_LIMIT):
            captcha_text = self._solve_captcha()
            search_bar = self._driver.find_element_by_css_selector("input#mtcap-inputtext-1")
            search_bar.send_keys(captcha_text)
            time.sleep(3)
            solve_text = self._driver.find_element_by_css_selector("span.mtcap-hidden-aria").text
            if solve_text == "captcha verified successfully.":
                self._driver.switch_to.default_content()
                token = self._driver.find_element_by_css_selector("input.mtcaptcha-verifiedtoken").get_attribute(
                    "value"
                )
                return token
        self._driver.switch_to.default_content()
        raise GeneralFatalError(reason="<anti-captcha-error>")

    def _solve_captcha(self):
        response = scrapy.Selector(text=self.get_page_source())
        src = response.css("img.mtcap-show-if-nocss::attr(src)").get()
        pattern = re.compile(r"data:image/png;base64,(?P<base64>.+)$")
        base64_match = pattern.match(src)
        if base64_match:
            base64_str = base64_match.group("base64")
            image_content = base64.b64decode(base64_str)
        else:
            return ""

        captcha_solver = ImageAntiCaptchaService()
        return captcha_solver.solve(image_content)
