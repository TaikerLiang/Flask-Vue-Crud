from datetime import date
import time
from typing import Dict, List
from urllib.parse import urlencode


import scrapy
from scrapy.http import Response
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from crawler.core_terminal.base_spiders import BaseMultiTerminalSpider
from crawler.core_terminal.exceptions import TerminalInvalidContainerNoError
from crawler.core_terminal.items import DebugItem, TerminalItem, InvalidContainerNoItem, InvalidDataFieldItem
from crawler.core_terminal.ptp_share_spider import ContainerRoutingRule
from crawler.core_terminal.request_helpers import RequestOption
from crawler.core_terminal.rules import RuleManager, BaseRoutingRule
from crawler.core.selenium import ChromeContentGetter

BASE_URL = "http://webaccess.gaports.com/express/"


class GpaShareSpider(BaseMultiTerminalSpider):
    firms_code = ""
    name = ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        rules = [
            LoginRoutingRule(),
            ToContainerPageRoutingRule(),
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
            if True in [isinstance(result, item) for item in [TerminalItem, InvalidDataFieldItem]]:
                c_no = result.get("container_no")
                t_ids = self.cno_tid_map.get(c_no)
                if t_ids != None:
                    for t_id in t_ids:
                        result["task_id"] = t_id
                        yield result
            elif isinstance(result, InvalidContainerNoItem):
                result["task_id"] = self.task_ids
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
                method="GET",
                url=option.url,
                headers=option.headers,
                meta=meta,
                cookies=option.cookies,
            )
        elif option.method == RequestOption.METHOD_POST_BODY:
            return scrapy.Request(
                method="POST",
                url=option.url,
                headers=option.headers,
                body=option.body,
                meta=meta,
                cookies=option.cookies,
            )
        else:
            raise RuntimeError()


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
        container_no_list = response.meta.get("container_no_list")
        browser = ContentGetter()
        browser.login()
        cookies = browser.get_cookies_dict()
        browser.close()

        yield ToContainerPageRoutingRule.build_request_option(container_no_list=container_no_list, cookies=cookies)


class ToContainerPageRoutingRule(BaseRoutingRule):
    name = "To_Container_Page"

    @classmethod
    def build_request_option(cls, container_no_list: List, cookies: Dict) -> RequestOption:
        url = BASE_URL + "displayReport.do?param=DeliveryInq"

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=url,
            cookies=cookies,
            meta={"container_no_list": container_no_list, "cookies": cookies},
        )

    def get_save_name(self, response) -> str:
        return f"{self.name}.json"

    def handle(self, response):
        container_no_list = response.meta.get("container_no_list")
        cookies = response.meta.get("cookies")

        yield ContainerRoutingRule.build_request_option(container_no_list, cookies)


class ContainerRoutingRule(BaseRoutingRule):
    name = "Container"

    @classmethod
    def build_request_option(cls, container_no_list: List, cookies: Dict) -> RequestOption:
        url = BASE_URL + "displayReport.do"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Cookie": f"JSESSIONID={cookies.get('JSESSIONID')}",
        }
        body = {
            "eqNbrs": "\n".join(container_no_list),
            "trkcID": "ANY",
            "pickupDate": date.today().strftime("%d-%b-%Y"),
            "param": "DeliveryInq",
            "submitted": "true",
        }

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_POST_BODY,
            url=url,
            headers=headers,
            body=urlencode(body),
            cookies=cookies,
            meta={"container_no_list": container_no_list, "cookies": cookies},
        )

    def get_save_name(self, response) -> str:
        return f"{self.name}.json"

    def handle(self, response):
        container_no_list = response.meta.get("container_no_list")
        try:
            table = self._get_table_list(response)
        except TerminalInvalidContainerNoError:
            yield InvalidContainerNoItem(container_no=container_no_list)
        else:
            info_list = self._extract_info_list(table)
            for info in info_list:
                if info.get("invalid"):
                    yield info.get("invalid")
                else:
                    yield TerminalItem(
                        container_no=info.get("container_no"),
                        available=info.get("available"),
                        carrier_release=info.get("line_release"),
                        customs_release=info.get("customs_release"),
                    )

    def _get_table_list(self, response: Response) -> List[List]:
        tr_selector = response.css("tbody[class='tablebody1'] tr")
        if len(tr_selector) == 1 and tr_selector[0].css("td::text").get() == "No items found for this table.":
            raise TerminalInvalidContainerNoError

        table = []
        for tr in tr_selector:
            data = []
            data.append(tr.css("td:nth-child(1) img::attr(title)").get())
            data.append(tr.css("td:nth-child(2) a::text").get())
            data.extend(tr.css("td::text").getall())
            table.append(data)

        return table

    def _extract_info_list(self, table: List[List]) -> List[Dict]:
        info_list = []
        for row in table:
            available = row[0]
            container_no = row[1]
            location = row[5]
            line_status = row[7]
            customs_status = row[8]

            invalid_item = self._check_data_validability(available, container_no, location, line_status, customs_status)
            if invalid_item:
                info_list.append({"invalid": invalid_item})
                continue

            info = {}

            info["container_no"] = container_no

            if available == "Yes":
                info["available"] = True
            elif available == "No":
                info["available"] = False

            if line_status == "RELEASED":
                info["line_release"] = True
            else:
                info["line_release"] = False

            if customs_status == "RELEASED":
                info["customs_release"] = True
            else:
                info["customs_release"] = False

            info_list.append(info)

        return info_list

    def _check_data_validability(self, available, container_no, location, line_status, customs_status):
        invalid_data_field_item = InvalidDataFieldItem(
            container_no=container_no, valid_data_dict={}, invalid_data_dict={}
        )

        if available != "Yes" and available != "No":
            invalid_data_field_item["valid_data_dict"].update({"available": ["Yes", "No"]})
            invalid_data_field_item["invalid_data_dict"].update({"available": available})

        if location != "C" and location != "V" and location != "Y":
            invalid_data_field_item["valid_data_dict"].update({"location": ["C", "V", "Y"]})
            invalid_data_field_item["invalid_data_dict"].update({"location": location})

        if line_status != "RELEASED" and line_status != "HOLD":
            invalid_data_field_item["valid_data_dict"].update({"line_status": ["RELEASE", "HOLD"]})
            invalid_data_field_item["invalid_data_dict"].update({"line_status": line_status})

        if customs_status != "RELEASED" and customs_status != "HOLD":
            invalid_data_field_item["valid_data_dict"].update({"customs_status": ["RELEASE", "HOLD"]})
            invalid_data_field_item["invalid_data_dict"].update({"customs_status": customs_status})

        if invalid_data_field_item["valid_data_dict"]:
            return invalid_data_field_item
        else:
            return None


class ContentGetter(ChromeContentGetter):
    USERNAME = "cli2"
    PASSWORD = "Hardc0re"
    LOGIN_URL = BASE_URL + "secure/Today.jsp?Facility=GCT"

    def login(self):
        self._driver.get(self.LOGIN_URL)
        time.sleep(10)
        WebDriverWait(self._driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='j_username']"))
        )
        self._driver.find_element_by_css_selector("input[name='j_username']").send_keys(self.USERNAME)
        self._driver.find_element_by_css_selector("input[name='j_password']").send_keys(self.PASSWORD)

        login_btn = WebDriverWait(self._driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@name='submit'][text()='Log In']"))
        )
        login_btn.click()
        time.sleep(10)