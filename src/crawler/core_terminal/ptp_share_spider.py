import json
import time
from typing import Dict, List

import scrapy
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from crawler.core_terminal.base_spiders import BaseMultiTerminalSpider
from crawler.core_terminal.items import DebugItem, TerminalItem, InvalidContainerNoItem
from crawler.core_terminal.request_helpers import RequestOption
from crawler.core_terminal.rules import RuleManager, BaseRoutingRule
from crawler.core_terminal.exceptions import TerminalInvalidContainerNoError
from crawler.core.selenium import ChromeContentGetter

BASE_URL = "https://www.porttruckpass.com"


class PtpShareSpider(BaseMultiTerminalSpider):
    firms_code = ""
    name = ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        rules = [
            LoginRoutingRule(),
            GetContainerNoRoutingRule(),
            RemoveContainerNoRoutingRule(),
            ContainerRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)

    def start(self):
        unique_container_nos = list(self.cno_tid_map.keys())
        option = LoginRoutingRule.build_request_option(container_no_list=unique_container_nos)
        yield self._build_request_by(option=option)

    def parse(self, response):
        yield DebugItem(info={"meta": dict(response.meta)})

        routing_rule = self._rule_manager.get_rule_by_response(response=response)

        save_name = routing_rule.get_save_name(response=response)
        self._saver.save(to=save_name, text=response.text)

        for result in routing_rule.handle(response=response):
            if isinstance(result, TerminalItem) or isinstance(result, InvalidContainerNoItem):
                c_no = result["container_no"]
                t_ids = self.cno_tid_map.get(c_no)
                if t_ids != None:
                    for t_id in t_ids:
                        result["task_id"] = t_id
                        yield result
            elif isinstance(result, RequestOption):
                yield self._build_request_by(option=result)
            else:
                raise RuntimeError()

    def _build_request_by(self, option: RequestOption):
        meta = {
            RuleManager.META_TERMINAL_CORE_RULE_NAME: option.rule_name,
            **option.meta,
        }

        if option.method == RequestOption.METHOD_GET:
            return scrapy.Request(
                method=RequestOption.METHOD_GET,
                url=option.url,
                headers=option.headers,
                meta=meta,
                cookies=option.cookies,
            )

        else:
            raise RuntimeError()


# -------------------------------------------------------------------------------
class LoginRoutingRule(BaseRoutingRule):
    name = "Login"

    @classmethod
    def build_request_option(cls, container_no_list: List[str]) -> RequestOption:
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url="https://www.google.com",
            meta={
                "container_no_list": container_no_list,
            },
        )

    def get_save_name(self, response) -> str:
        return f"{self.name}.html"

    def handle(self, response):
        container_no_list = response.meta["container_no_list"]
        browser = ContentGetter(proxy_manager=None, is_headless=True)
        browser.login()
        cookies = browser.get_cookie_dict()
        browser.close()

        yield GetContainerNoRoutingRule.build_request_option(container_no_list=container_no_list, cookies=cookies)


# -------------------------------------------------------------------------------


class GetContainerNoRoutingRule(BaseRoutingRule):
    name = "Get_Container_No"

    @classmethod
    def build_request_option(cls, container_no_list: List, cookies: Dict) -> RequestOption:
        url = "https://www.porttruckpass.com:64455/ImportAvailability/GetContainerInfoList?sgrdModel=%7B%22searchtext%22:%22%22,%22page%22:1,%22pageSize%22:30,%22sortBy%22:%221%22,%22sortDirection%22:%22asc%22,%22sortColumns%22:%22%22%7D"
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_1_0) AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/87.0.4280.141 Safari/537.36"
                ),
                "Referer": "https://www.porttruckpass.com:64455/ImportAvailability",
                "Accept-Language": "zh-TW,zh;q=0.9",
            },
            cookies=cookies,
            meta={
                "container_no_list": container_no_list,
                "cookies": cookies,
            },
        )

    def get_save_name(self, response) -> str:
        return f"{self.name}.json"

    def handle(self, response):
        container_no_list = response.meta["container_no_list"]
        cookies = response.meta["cookies"]
        response_dict = json.loads(response.text)
        remove_container_nos = []
        for content in response_dict["Content"]:
            remove_container_nos.append(content["ContainerNumber"])
        yield RemoveContainerNoRoutingRule.build_request_option(container_no_list, remove_container_nos, cookies)


# -------------------------------------------------------------------------------


class RemoveContainerNoRoutingRule(BaseRoutingRule):
    name = "Remove_Container_No"

    @classmethod
    def build_request_option(cls, container_no_list: List, remove_container_nos: List, cookies: Dict) -> RequestOption:
        url = f"https://www.porttruckpass.com:64455/ImportAvailability/RemoveContainerWatchListInfo?Container_Nbr={','.join(remove_container_nos)}"
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_1_0) AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/87.0.4280.141 Safari/537.36"
                ),
                "Referer": "https://www.porttruckpass.com:64455/ImportAvailability",
                "Accept-Language": "zh-TW,zh;q=0.9",
            },
            cookies=cookies,
            meta={
                "container_no_list": container_no_list,
                "cookies": cookies,
            },
        )

    def get_save_name(self, response) -> str:
        return f"{self.name}.json"

    def handle(self, response):
        container_no_list = response.meta["container_no_list"]
        cookies = response.meta["cookies"]
        yield ContainerRoutingRule.build_request_option(container_no_list, cookies)


# -------------------------------------------------------------------------------


class ContainerRoutingRule(BaseRoutingRule):
    name = "Container"

    @classmethod
    def build_request_option(cls, container_no_list: List, cookies: Dict) -> RequestOption:
        url = (
            f"https://www.porttruckpass.com:64455/ImportAvailability/GetContainerInfoList?"
            f"apiParams=%7B%22Container_Nbr%22:%22{'%5Cn'.join(container_no_list)}%22%7D&"
            f"sgrdModel=%7B%22searchtext%22:%22%22,%22page%22:1,%22pageSize%22:20,%22sortBy%22:%221%22,%22sortDirection%22:%22asc%22,%22sortColumns%22:%22%22%7D"
        )
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_1_0) AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/87.0.4280.141 Safari/537.36"
                ),
                "Referer": "https://www.porttruckpass.com:64455/ImportAvailability",
                "Accept-Language": "zh-TW,zh;q=0.9",
            },
            cookies=cookies,
            meta={"container_no_list": container_no_list, "cookies": cookies},
        )

    def get_save_name(self, response) -> str:
        return f"{self.name}.json"

    def handle(self, response):
        container_no_list = response.meta["container_no_list"]
        response_dict = json.loads(response.text)
        for content in response_dict["Content"]:
            if content["ContainerInfo"] == "":
                raise TerminalInvalidContainerNoError
            container_info = json.loads(content["ContainerInfo"])
            yield TerminalItem(
                container_no=content["ContainerNumber"],
                available=content["AvailableStatus"],
                last_free_day=content["LastFreeDay"],
                gate_out_date=container_info["outgate-dt"],
                customs_release=container_info["custm-status"],
                demurrage=container_info["demurrage-status"],
                holds=content["Holds"],
                vessel=container_info["vsl"],
                voyage=container_info["voy"],
            )


# -------------------------------------------------------------------------------


class ContentGetter(ChromeContentGetter):
    USERNAME = "HardcoreTK"
    PASSWORD = "Hardc0re"

    def login(self):
        self._driver.get("https://www.porttruckpass.com/Default.aspx")
        time.sleep(10)
        WebDriverWait(self._driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input#txtUserName")))
        self._driver.find_element_by_css_selector("input#txtUserName").send_keys(self.USERNAME)
        self._driver.find_element_by_css_selector("input#txtPassword").send_keys(self.PASSWORD)

        login_btn = WebDriverWait(self._driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "input#btnLogin"))
        )
        login_btn.click()
        time.sleep(10)

    def get_cookie_dict(self):
        cookies = {}
        for cookie_object in self._driver.get_cookies():
            cookies[cookie_object["name"]] = cookie_object["value"]
        return cookies
