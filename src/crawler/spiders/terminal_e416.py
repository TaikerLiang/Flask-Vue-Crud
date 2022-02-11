import time
import json
from typing import List, Dict

from scrapy import Request, FormRequest
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from crawler.core.table import HeaderMismatchError
from crawler.core.selenium import ChromeContentGetter
from crawler.core_terminal.base_spiders import BaseMultiTerminalSpider
from crawler.core_terminal.exceptions import LoadWebsiteTimeOutFatal
from crawler.core_terminal.base import TERMINAL_RESULT_STATUS_ERROR
from crawler.core_terminal.items import DebugItem, TerminalItem, ExportErrorData
from crawler.core_terminal.rules import RuleManager, BaseRoutingRule, RequestOption


MAX_PAGE_NUM = 10
URL = "https://mahercsp.maherterminals.com"
EMAIL = "hard202006010"
PASSWORD = "hardc0re"


class MaherContentGetter(ChromeContentGetter):
    USERNAME = "hard202006010"
    PASSWORD = "hardc0re"

    def search(self, container_no_list: List):
        container_inquiry_text_area = self._driver.find_element_by_css_selector("textarea[name='equipment']")
        container_inquiry_text_area.clear()

        if len(container_no_list) == 1:
            container_no_list = container_no_list + container_no_list

        container_inquiry_text_area.send_keys("\n".join(container_no_list))

        search_btn = self._driver.find_element_by_css_selector("input[onclick='Search();']")
        search_btn.click()
        time.sleep(20)

        return self._driver.page_source

    def detail_search(self, container_no):
        self._driver.get(
            f"https://apps.maherterminals.com/csp/importContainerAction.do?container={container_no}&index=0&method=detail"
        )
        time.sleep(5)

        return self._driver.page_source

    def login(self):
        self._driver.get("https://apps.maherterminals.com/csp/loginAction.do?method=login")

        try:
            WebDriverWait(self._driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='userBean.username']"))
            )
        except TimeoutException:
            raise LoadWebsiteTimeOutFatal()

        username_input = self._driver.find_element_by_css_selector("input[name='userBean.username']")
        password_input = self._driver.find_element_by_css_selector("input[name='userBean.password']")

        username_input.send_keys(self.USERNAME)
        password_input.send_keys(self.PASSWORD)

        login_btn = self._driver.find_element_by_css_selector("input[name='cancelButton']")
        login_btn.click()
        time.sleep(5)

        self._driver.get(
            "https://apps.maherterminals.com/csp/importContainerAction.do?method=initial&pageTitle=Import%20Container%20Status%20Inquiry"
        )
        time.sleep(5)


class TerminalMaherMultiSpider(BaseMultiTerminalSpider):
    firms_code = "E416"
    name = "terminal_maher_multi"

    def __init__(self, *args, **kwargs):
        super(TerminalMaherMultiSpider, self).__init__(*args, **kwargs)

        rules = [
            LoginRoutingRule(),
            SearchRoutingRule(),
            NextRoundRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)
        self._max_retry_times = 3

    def start(self):
        unique_container_nos = list(self.cno_tid_map.keys())
        option = LoginRoutingRule.build_request_option(container_nos=unique_container_nos)
        yield self._build_request_by(option=option)

    def parse(self, response):
        yield DebugItem(info={"meta": dict(response.meta)})

        routing_rule = self._rule_manager.get_rule_by_response(response=response)

        save_name = routing_rule.get_save_name(response=response)
        self._saver.save(to=save_name, text=response.text)

        try:
            for result in routing_rule.handle(response=response):
                if isinstance(result, TerminalItem) or isinstance(result, ExportErrorData):
                    c_no = result["container_no"]
                    t_ids = self.cno_tid_map[c_no]
                    for t_id in t_ids:
                        result["task_id"] = t_id
                        yield result
                elif isinstance(result, RequestOption):
                    yield self._build_request_by(option=result)
                else:
                    raise RuntimeError()
        except HeaderMismatchError as e:
            self._max_retry_times -= 1

            # retry searching
            if self._max_retry_times >= 0:
                unique_container_nos = list(self.cno_tid_map.keys())
                option = SearchRoutingRule.build_request_option(container_no_list=unique_container_nos)
                yield self._build_request_by(option=option)
            else:
                raise HeaderMismatchError("Already consumed all retry times")

    def _build_request_by(self, option: RequestOption):
        meta = {
            RuleManager.META_TERMINAL_CORE_RULE_NAME: option.rule_name,
            **option.meta,
        }

        if option.method == RequestOption.METHOD_GET:
            return Request(
                url=option.url,
                headers=option.headers,
                meta=meta,
                dont_filter=True,
            )
        elif option.method == RequestOption.METHOD_POST_FORM:
            return FormRequest(
                url=option.url,
                formdata=option.form_data,
                headers=option.headers,
                meta=meta,
                dont_filter=True,
            )
        elif option.method == RequestOption.METHOD_POST_BODY:
            return Request(
                url=option.url,
                headers=option.headers,
                body=option.body,
                meta=meta,
                dont_filter=True,
                method="POST",
            )
        else:
            raise ValueError(f"Invalid option.method [{option.method}]")


# -------------------------------------------------------------------------------


class LoginRoutingRule(BaseRoutingRule):
    name = "LOGIN"

    @classmethod
    def build_request_option(cls, container_nos: List[str]) -> RequestOption:
        form_data = {"user": {"username": "HARD202006010", "password": "hardc0re"}, "requestData": []}

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_POST_BODY,
            url=f"{URL}/cspgateway/rest/services/userService/loginUser",
            headers={"Content-Type": "application/json"},
            body=json.dumps(form_data),
            meta={"container_nos": container_nos},
        )

    def handle(self, response):
        container_nos = response.meta["container_nos"]
        user_data = json.loads(response.text)
        token = response.headers.get("Authorization").decode("utf-8")

        yield SearchRoutingRule.build_request_option(container_nos=container_nos, user_data=user_data, token=token)


class SearchRoutingRule(BaseRoutingRule):
    name = "SEARCH"

    @classmethod
    def build_request_option(cls, container_nos: List[str], user_data: Dict, token: str) -> RequestOption:
        form_data = {"user": user_data, "requestData": [{"container": ct} for ct in container_nos[:MAX_PAGE_NUM]]}

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_POST_BODY,
            url=f"{URL}/cspgateway/rest/services/importInquiryService/getContainers",
            headers={
                "Content-Type": "application/json",
                "Referer": "https://mahercsp.maherterminals.com/CSP/importContainers",
                "Authorization": token,
            },
            body=json.dumps(form_data),
            meta={
                "container_nos": container_nos,
                "user_data": user_data,
                "token": token,
            },
        )

    def get_save_name(self, response) -> str:
        return f"{self.name}.html"

    def handle(self, response):
        container_nos = response.meta["container_nos"]
        user_data = response.meta["user_data"]
        token = response.meta["token"]
        containers_resp = json.loads(response.text)

        print(containers_resp)

        for resp in containers_resp:
            if resp.get("maherError", ""):
                yield ExportErrorData(
                    container_no=resp["container"],
                    status=TERMINAL_RESULT_STATUS_ERROR,
                    detail="Data was not found",
                )
                continue

            yield TerminalItem(
                container_no=resp["container"],
                available=resp.get("available", ""),
                customs_release=resp.get("customs_released_description", ""),
                discharge_date=resp.get("received_date_fmt", ""),
                last_free_day=resp.get("fte_date_fmt", ""),
                carrier_release=("Yes" if resp.get("freight_released", "") == "1" else "No"),
            )

        yield NextRoundRoutingRule.build_request_option(container_nos=container_nos, user_data=user_data, token=token)


# -------------------------------------------------------------------------------


class NextRoundRoutingRule(BaseRoutingRule):
    name = "NEXT_ROUND"

    @classmethod
    def build_request_option(cls, container_nos: List, user_data: Dict, token: str) -> RequestOption:
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url="http://tracking.hardcoretech.co:18110",
            meta={
                "container_nos": container_nos,
                "user_data": user_data,
                "token": token,
                "handle_httpstatus_list": [404],
            },
        )

    def handle(self, response):
        container_nos = response.meta["container_nos"]
        user_data = response.meta["user_data"]
        token = response.meta["token"]

        if len(container_nos) <= MAX_PAGE_NUM:
            return

        container_nos = container_nos[MAX_PAGE_NUM:]

        yield SearchRoutingRule.build_request_option(container_nos=container_nos, user_data=user_data, token=token)
