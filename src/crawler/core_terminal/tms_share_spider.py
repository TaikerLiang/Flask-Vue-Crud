import dataclasses
from typing import Dict, List
import time
from crawler.core.selenium import ChromeContentGetter
from crawler.core.table import BaseTable, TableExtractor

import scrapy
from scrapy import Selector

from crawler.core.base import DUMMY_URL_DICT
from crawler.core_terminal.base_spiders import BaseMultiTerminalSpider
from crawler.core_terminal.exceptions import TerminalResponseFormatError
from crawler.core_terminal.items import DebugItem, TerminalItem, InvalidContainerNoItem
from crawler.core_terminal.request_helpers import RequestOption
from crawler.core_terminal.rules import RuleManager, BaseRoutingRule
from crawler.extractors.table_cell_extractors import BaseTableCellExtractor

BASE_URL = "https://tms.itslb.com"
MAX_PAGE_NUM = 20


@dataclasses.dataclass
class CompanyInfo:
    email: str
    password: str


class TmsSharedSpider(BaseMultiTerminalSpider):
    name = None
    terminal_id = None
    company_info = CompanyInfo(
        email="",
        password="",
    )

    def __init__(self, *args, **kwargs):
        super(TmsSharedSpider, self).__init__(*args, **kwargs)

        rules = [
            SeleniumRoutingRule(),
            NextRoundRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)

    def start(self):
        unique_container_nos = list(self.cno_tid_map.keys())
        request_option = SeleniumRoutingRule.build_request_option(
            container_nos=unique_container_nos, terminal_id=self.terminal_id, company_info=self.company_info
        )
        yield self._build_request_by(option=request_option)

    def parse(self, response):
        yield DebugItem(info={"meta": dict(response.meta)})

        routing_rule = self._rule_manager.get_rule_by_response(response=response)

        save_name = routing_rule.get_save_name(response=response)
        self._saver.save(to=save_name, text=response.text)

        for result in routing_rule.handle(response=response):
            if isinstance(result, TerminalItem) or isinstance(result, InvalidContainerNoItem):
                c_no = result["container_no"]
                t_ids = self.cno_tid_map[c_no]
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
                url=option.url,
                headers=option.headers,
                meta=meta,
                dont_filter=True,
            )
        else:
            raise ValueError(f"Invalid option.method [{option.method}]")


class SeleniumRoutingRule(BaseRoutingRule):
    name = "SELENIUM"

    @classmethod
    def build_request_option(cls, container_nos: List, terminal_id: int, company_info) -> RequestOption:
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url="https://www.google.com",
            meta={
                "container_nos": container_nos,
                "terminal_id": terminal_id,
                "company_info": company_info,
            },
        )

    def handle(self, response):
        container_nos = response.meta["container_nos"]
        terminal_id = response.meta["terminal_id"]
        company_info = response.meta["company_info"]

        content_getter = ContentGetter(proxy_manager=None, is_headless=True)
        content_getter.login(company_info.email, company_info.password)
        content_getter.select_terminal(terminal_id)

        # TODO: can improve here, send request one time
        for container_no in container_nos[:MAX_PAGE_NUM]:
            page_source = content_getter.search(container_no)
            resp = Selector(text=page_source)
            if not resp.css("table.table-borderless"):
                continue

            for item in self._handle_response(response=resp):
                yield item

        content_getter.close()

        yield NextRoundRoutingRule.build_request_option(
            container_nos=container_nos, terminal_id=terminal_id, company_info=company_info
        )

    @classmethod
    def _handle_response(cls, response):
        container_info = cls._extract_container_info(response)
        extra_container_info = cls._extract_extra_container_info(response)

        yield TerminalItem(
            container_no=container_info["container_no"],
            carrier_release=extra_container_info["freight_release"],
            customs_release=extra_container_info["customs_release"],
            appointment_date=container_info["appointment_date"],
            ready_for_pick_up=container_info["ready_for_pick_up"],
            last_free_day=container_info["last_free_day"],
            demurrage=extra_container_info["demurrage"],
            carrier=container_info["carrier"],
            container_spec=container_info["container_spec"],
            vessel=extra_container_info["vessel"],
            mbl_no=extra_container_info["mbl_no"],
            voyage=extra_container_info["voyage"],
            gate_out_date=extra_container_info["gate_out_date"],
            chassis_no=container_info["chassis_no"],
        )

    @staticmethod
    def _extract_container_info(response: scrapy.Selector) -> Dict:
        table_selector = response.css("table.table-borderless")

        if table_selector is None:
            raise TerminalResponseFormatError(reason="Container info table not found")

        table_locator = TopInfoTableLocator()
        table_locator.parse(table=table_selector)
        table = TableExtractor(table_locator=table_locator)

        for left in table_locator.iter_left_header():
            return {
                "appointment_date": table.extract_cell("Dschg Date", left),
                "ready_for_pick_up": table.extract_cell("Pick Up", left),
                "last_free_day": table.extract_cell("LFD", left),
                "container_no": table.extract_cell("Container#", left, TdSpanExtractor()),
                "carrier": table.extract_cell("Line", left),
                "container_spec": table.extract_cell("SzTpHt", left),
                "chassis_no": table.extract_cell("Chassis#", left),
            }

    @staticmethod
    def _extract_extra_container_info(response: scrapy.Selector) -> Dict:
        table_selector = response.css("table.table-bordered")

        if table_selector is None:
            raise TerminalResponseFormatError(reason="Extra container info table not found")

        left_table_locator = LeftExtraContainerLocator()
        left_table_locator.parse(table=table_selector)
        left_table = TableExtractor(table_locator=left_table_locator)

        middle_table_locator = MiddleExtraContainerLocator()
        middle_table_locator.parse(table=table_selector)
        middle_table = TableExtractor(table_locator=middle_table_locator)

        right_table_locator = RightExtraContainerLocator()
        right_table_locator.parse(table=table_selector)
        right_table = TableExtractor(table_locator=right_table_locator)

        return {
            "vessel": left_table.extract_cell(left=0, top="Vessel"),
            "customs_release": left_table.extract_cell(left=0, top="Customs"),
            "freight_release": left_table.extract_cell(left=0, top="Freight"),
            "voyage": middle_table.extract_cell(left=0, top="Voyage"),
            "gate_out_date": middle_table.extract_cell(left=0, top="Spot"),
            "mbl_no": right_table.extract_cell(left=0, top="B/L#"),
            "demurrage": right_table.extract_cell(left=0, top="Demurrage"),
        }


class NextRoundRoutingRule(BaseRoutingRule):
    name = "NEXT_ROUND"

    @classmethod
    def build_request_option(cls, container_nos: List, terminal_id: int, company_info) -> RequestOption:
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=DUMMY_URL_DICT["google"],
            meta={
                "container_nos": container_nos,
                "terminal_id": terminal_id,
                "company_info": company_info,
            },
        )

    def handle(self, response):
        container_nos = response.meta["container_nos"]
        terminal_id = response.meta["terminal_id"]
        company_info = response.meta["company_info"]

        if len(container_nos) <= MAX_PAGE_NUM:
            return

        container_nos = container_nos[MAX_PAGE_NUM:]

        yield SeleniumRoutingRule.build_request_option(
            container_nos=container_nos, terminal_id=terminal_id, company_info=company_info
        )


class TopInfoTableLocator(BaseTable):
    """
    +---------+---------+-----+---------+ <table>
    | Title 1 | Title 2 | ... | Title N | <tr>
    +---------+---------+-----+---------+
    | Data 1  | Data 2  | ... | Data N  | <tr>
    +---------+---------+-----+---------+
    | extra container info table        | <tr>
    +-----------------------------------+ </table>
    """

    TR_TITLE_INDEX = 0
    TR_DATA_INDEX_BEGIN = 1
    TR_DATA_INDEX_END = 2

    def parse(self, table: Selector):
        title_tr = table.css("tr")[self.TR_TITLE_INDEX]
        title_text_list = [title.strip() for title in title_tr.css("th a::text").getall()]

        data_tr_list = table.css("tr")[self.TR_DATA_INDEX_BEGIN : self.TR_DATA_INDEX_END]

        for index, tr in enumerate(data_tr_list):
            tds = tr.css("td")
            self._left_header_set.add(index)
            for title, td in zip(title_text_list, tds):
                self._td_map.setdefault(title, [])
                self._td_map[title].append(td)


class TdSpanExtractor(BaseTableCellExtractor):
    def extract(self, cell: Selector) -> str:
        td_text = cell.css("span::text").get()
        return td_text.strip() if td_text else ""


class LeftExtraContainerLocator(BaseTable):
    """
    +---------+--------+-----+-----+-----+-----+ <table>
    | Title 1 | Data 1 |     |     |     |     | <tr>
    +---------+--------+-----+-----+-----+-----+
    | Title 2 | Data 2 |     |     |     |     | <tr>
    +---------+--------+-----+-----+-----+-----+
    | ...     | ...    |     |     |     |     | <tr>
    +---------+--------+-----+-----+-----+-----+
    | Title N | Data N |     |     |     |     | <tr>
    +---------+--------+-----+-----+-----+-----+ </table>
    """

    TR_CONTENT_BEGIN_INDEX = 0
    TD_TITLE_INDEX = 0
    TD_DATA_INDEX = 1

    def parse(self, table: scrapy.Selector):
        content_tr_list = table.css("tr")[self.TR_CONTENT_BEGIN_INDEX :]
        self._left_header_set.add(0)  # if multi tables are to be processed in one request, refactor is required here

        for tr in content_tr_list:
            title_td = tr.css("td")[self.TD_TITLE_INDEX]
            data_td = tr.css("td")[self.TD_DATA_INDEX]

            title_text = title_td.css("::text").get().strip()

            self._td_map.setdefault(title_text, [])
            self._td_map[title_text].append(data_td)


class MiddleExtraContainerLocator(BaseTable):
    """
    +-----+-----+---------+--------+-----+-----+ <table>
    |     |     | Title 1 | Data 1 |     |     | <tr>
    +-----+-----+---------+--------+-----+-----+
    |     |     | Title 2 | Data 2 |     |     | <tr>
    +-----+-----+---------+--------+-----+-----+
    |     |     | ...     | ...    |     |     | <tr>
    +-----+-----+---------+--------+-----+-----+
    |     |     | Title N | Data N |     |     | <tr>
    +-----+-----+---------+--------+-----+-----+ </table>
    """

    TR_CONTENT_BEGIN_INDEX = 0
    TR_CONTENT_END_INDEX = 3
    TD_TITLE_INDEX = 2
    TD_DATA_INDEX = 3

    def parse(self, table: scrapy.Selector):
        content_tr_list = table.css("tr")[self.TR_CONTENT_BEGIN_INDEX : self.TR_CONTENT_END_INDEX]
        self._left_header_set.add(0)  # if multi tables are to be processed in one request, refactor is required here

        for tr in content_tr_list:
            title_td = tr.css("td")[self.TD_TITLE_INDEX]
            data_td = tr.css("td")[self.TD_DATA_INDEX]

            title_text = title_td.css("::text").get().strip()

            self._td_map.setdefault(title_text, [])
            self._td_map[title_text].append(data_td)


class RightExtraContainerLocator(BaseTable):
    """
    +-----+-----+-----+-----+---------+--------+ <table>
    |     |     |     |     | Title 1 | Data 1 | <tr>
    +-----+-----+-----+-----+---------+--------+
    |     |     |     |     | Title 2 | Data 2 | <tr>
    +-----+-----+-----+-----+---------+--------+
    |     |     |     |     | ...     | ...    | <tr>
    +-----+-----+-----+-----+---------+--------+
    |     |     |     |     | Title N | Data N | <tr>
    +-----+-----+-----+-----+---------+--------+ </table>
    """

    TR_CONTENT_BEGIN_INDEX = 0
    TR_CONTENT_END_INDEX = 4
    TD_TITLE_INDEX = 4
    TD_DATA_INDEX = 5

    def parse(self, table: scrapy.Selector):
        content_tr_list = table.css("tr")[self.TR_CONTENT_BEGIN_INDEX : self.TR_CONTENT_END_INDEX]
        self._left_header_set.add(0)  # if multi tables are to be processed in one request, refactor is required here

        for tr in content_tr_list:
            title_td = tr.css("td")[self.TD_TITLE_INDEX]
            data_td = tr.css("td")[self.TD_DATA_INDEX]

            title_text = title_td.css("::text").get().strip()

            self._td_map.setdefault(title_text, [])
            self._td_map[title_text].append(data_td)


class ContentGetter(ChromeContentGetter):
    def login(self, username: str, password: str):
        self._driver.get("https://tms.itslb.com/tms2/Account/Login")
        time.sleep(7)
        username_input = self._driver.find_element_by_xpath('//*[@id="UserName"]')
        username_input.send_keys(username)
        time.sleep(1)
        password_input = self._driver.find_element_by_xpath('//*[@id="Password"]')
        password_input.send_keys(password)
        time.sleep(1)

        btn = self._driver.find_element_by_xpath('//*[@id="loginForm"]/form/div[6]/div/input')
        btn.click()
        time.sleep(7)

    def select_terminal(self, terminal_id: int):
        if terminal_id == 1:
            self._driver.find_element_by_xpath('//*[@id="loginTerminalId"]/option[1]').click()
        elif terminal_id == 3:
            self._driver.find_element_by_xpath('//*[@id="loginTerminalId"]/option[2]').click()
        time.sleep(7)

    def search(self, container_no: str):
        self._driver.get("https://tms.itslb.com/tms2/Import/ContainerAvailability")
        time.sleep(3)

        textarea = self._driver.find_element_by_xpath('//*[@id="refNums"]')
        textarea.send_keys(container_no)
        time.sleep(1)

        btn = self._driver.find_element_by_xpath('//*[@id="formAvailabilityHeader"]/div/div[1]/div/div[2]/div/button')
        btn.click()
        time.sleep(7)

        return self._driver.page_source
