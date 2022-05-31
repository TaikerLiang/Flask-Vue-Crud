import dataclasses
import re
import time
from typing import List

import scrapy
from scrapy import Selector

from crawler.core.selenium import ChromeContentGetter
from crawler.core.table import TableExtractor
from crawler.core_terminal.base import TERMINAL_RESULT_STATUS_ERROR
from crawler.core_terminal.base_spiders import BaseMultiTerminalSpider
from crawler.core_terminal.items import DebugItem, ExportErrorData, TerminalItem
from crawler.core_terminal.request_helpers import RequestOption
from crawler.core_terminal.rules import BaseRoutingRule, RuleManager
from crawler.extractors.table_cell_extractors import FirstTextTdExtractor
from crawler.extractors.table_extractors import TopHeaderTableLocator
from crawler.utils.container_no_checker import ContainerNoChecker

BASE_URL = "https://voyagertrack.portsamerica.com"
MAX_PAGE_NUM = 20


@dataclasses.dataclass
class CompanyInfo:
    upper_short: str
    email: str
    password: str


@dataclasses.dataclass
class WarningMessage:
    msg: str


class PortsamericaShareSpider(BaseMultiTerminalSpider):
    name = ""
    company_info = CompanyInfo(
        upper_short="",
        email="",
        password="",
    )

    def __init__(self, *args, **kwargs):
        super(PortsamericaShareSpider, self).__init__(*args, **kwargs)

        rules = [SearchContainerRule()]

        self._rule_manager = RuleManager(rules=rules)

    def start(self):
        unique_container_nos = list(self.cno_tid_map.keys())
        request_option = SearchContainerRule.build_request_option(
            container_no_list=unique_container_nos, company_info=self.company_info
        )
        yield self._build_request_by(option=request_option)

    def parse(self, response):
        yield DebugItem(info={"meta": dict(response.meta)})

        routing_rule = self._rule_manager.get_rule_by_response(response=response)

        save_name = routing_rule.get_save_name(response=response)
        self._saver.save(to=save_name, text=response.text)

        for result in routing_rule.handle(response=response):
            if isinstance(result, TerminalItem) or isinstance(result, ExportErrorData):
                c_no = result["container_no"]
                t_ids = self.cno_tid_map[c_no]
                for t_id in t_ids:
                    result["task_id"] = t_id
                    yield result
            elif isinstance(result, RequestOption):
                yield self._build_request_by(option=result)
            elif isinstance(result, WarningMessage):
                self.logger.warning(msg=result.msg)
            else:
                raise RuntimeError()

    def _build_request_by(self, option: RequestOption):
        meta = {
            RuleManager.META_TERMINAL_CORE_RULE_NAME: option.rule_name,
            **option.meta,
        }
        if option.method == RequestOption.METHOD_GET:
            return scrapy.Request(
                url=option.url,
                meta=meta,
            )
        else:
            raise RuntimeError()


class SearchContainerRule(BaseRoutingRule):
    name = "SEARCH"

    @classmethod
    def build_request_option(cls, container_no_list: List, company_info: CompanyInfo) -> RequestOption:
        url = "https://google.com"
        return RequestOption(
            method=RequestOption.METHOD_GET,
            rule_name=cls.name,
            url=url,
            meta={"container_no_list": container_no_list, "company_info": company_info},
        )

    def handle(self, response):
        company_info = response.meta["company_info"]
        container_no_list = response.meta["container_no_list"]

        content_getter = ContentGetter(proxy_manager=None, is_headless=True)
        content_getter.login(company_info.email, company_info.password, company_info.upper_short)

        while True:
            resp = content_getter.search(container_no_list[:MAX_PAGE_NUM])
            for item in self._handle_response(Selector(text=resp), container_no_list[:MAX_PAGE_NUM]):
                yield item

            if len(container_no_list) <= MAX_PAGE_NUM:
                content_getter.quit()
                break

            container_no_list = container_no_list[MAX_PAGE_NUM:]

    @classmethod
    def _handle_response(cls, response, container_no_list):
        containers = cls._extract_container_info(response, len(container_no_list))
        for container in containers:
            for container_no in container_no_list:
                if container["container_no"] == ContainerNoChecker.get_checked_no(container_no):
                    container_no_list.remove(container_no)
                    container["container_no"] = container_no

                    yield TerminalItem(
                        **container,
                    )

        for container_no in container_no_list:
            yield ExportErrorData(
                container_no=container_no,
                detail="Data was not found",
                status=TERMINAL_RESULT_STATUS_ERROR,
            )

    @staticmethod
    def _extract_container_info(resp: Selector, numbers: int):
        table = resp.xpath('//*[@id="divImportContainerGridPanel"]/div[1]/table')
        locator = TopHeaderTableLocator()
        locator.parse(table)
        extractor = TableExtractor(locator)
        available_extractor = FirstTextTdExtractor(css_query="label::text")
        res = []

        for row in locator.iter_left_header():
            appointment_date = extractor.extract_cell("Appointment Time", row)
            gate_out_date = extractor.extract_cell("Current State", row)

            if re.search("([0-9]+/[0-9]+/[0-9]{4}[0-9]{4}-[0-9]{4})", appointment_date):
                date_split_list = appointment_date.split("/")
                time_split_list = date_split_list[-1][4:].split("-")
                date_split_list[-1] = date_split_list[-1][:4]
                appointment_date = "/".join(date_split_list) + " " + time_split_list[0]

            if re.search("([0-9]+/[0-9]+/[0-9]{4} [0-9]+:[0-9]{2})", gate_out_date):
                date_split_list = gate_out_date.split("\n")
                gate_out_date = date_split_list[-1]

            gate_out_date = re.sub(r"\s{2,}", " ", gate_out_date)

            res.append(
                {
                    "container_no": extractor.extract_cell("Container Number", row).strip().replace("-", ""),
                    "ready_for_pick_up": extractor.extract_cell("Available", row).strip().replace("\xa0", " "),
                    "available": extractor.extract_cell("Available", row, available_extractor)
                    .strip()
                    .replace("\xa0", " "),
                    "yard_location": extractor.extract_cell("Current State", row),
                    "gate_out_date": gate_out_date,
                    "appointment_date": appointment_date.strip(),
                    "customs_release": extractor.extract_cell("Customs Status", row).strip(),
                    "carrier_release": extractor.extract_cell("Freight Status", row).strip(),
                    "holds": extractor.extract_cell("Misc. Holds", row).strip(),
                    "demurrage": extractor.extract_cell("Demurrage Amount", row).strip(),
                    "last_free_day": extractor.extract_cell("Last Free Day", row).strip(),
                    "carrier": extractor.extract_cell("SSCO", row).strip(),
                    "container_spec": extractor.extract_cell("Type", row).strip(),
                }
            )

        return res


class ContentGetter(ChromeContentGetter):
    def __init__(self, proxy_manager, is_headless):
        super().__init__(proxy_manager=proxy_manager, is_headless=is_headless)
        self.search_url = None

    def login(self, username, password, upper_short):
        url = f"{BASE_URL}/logon?siteId={upper_short}"
        self._driver.get(url)
        time.sleep(5)
        username_input = self._driver.find_element_by_xpath('//*[@id="UserName"]')
        username_input.send_keys(username)
        time.sleep(2)
        password_input = self._driver.find_element_by_xpath('//*[@id="Password"]')
        password_input.send_keys(password)
        time.sleep(2)
        login_btn = self._driver.find_element_by_xpath('//*[@id="btnLogonSubmit"]')
        login_btn.click()
        time.sleep(10)

    def search(self, container_no_list):
        if not self.search_url:
            self.search_url = f"{self._driver.current_url}#/Report/ImportContainer"
        self._driver.get(self.search_url)
        time.sleep(5)

        multi_search_btn = self._driver.find_element_by_xpath('//*[@id="imgOpenContainerMultipleEntryDialog"]')
        multi_search_btn.click()
        time.sleep(3)

        container_text_area = self._driver.find_element_by_xpath('//*[@id="ContainerNumbers"]')
        container_text_area.send_keys("\n".join(container_no_list))

        time.sleep(3)
        search_btn = self._driver.find_element_by_xpath('//*[@id="btnContainerSubmitMulti"]')
        search_btn.click()
        time.sleep(8)

        return self._driver.page_source
