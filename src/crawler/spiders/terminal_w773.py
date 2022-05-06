import re
from typing import List

from scrapy import FormRequest, Request, Selector

from crawler.core.table import BaseTable, TableExtractor
from crawler.core_terminal.base import TERMINAL_RESULT_STATUS_ERROR
from crawler.core_terminal.base_spiders import BaseMultiTerminalSpider
from crawler.core_terminal.items import (
    BaseTerminalItem,
    DebugItem,
    ExportErrorData,
    TerminalItem,
)
from crawler.core_terminal.rules import BaseRoutingRule, RequestOption, RuleManager

BASE_URL = "http://www.asocfs.com"
MAX_PAGE_NUM = 1


class TerminalAsoSpider(BaseMultiTerminalSpider):
    firms_code = ""
    name = "terminal_aso"

    def __init__(self, *args, **kwargs):
        super(TerminalAsoSpider, self).__init__(*args, **kwargs)

        rules = [
            QueryNoRoutingRule(),
            ContainerRoutingRule(),
            NextRoundRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)

    def start(self):
        option = QueryNoRoutingRule.build_request_option(container_nos=self.container_nos)
        yield self._build_request_by(option=option)

    def parse(self, response):
        yield DebugItem(info={"meta": dict(response.meta)})

        routing_rule = self._rule_manager.get_rule_by_response(response=response)

        save_name = routing_rule.get_save_name(response=response)
        self._saver.save(to=save_name, text=response.text)

        for result in routing_rule.handle(response=response):
            if isinstance(result, BaseTerminalItem):
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
        else:
            raise ValueError(f"Invalid option.method [{option.method}]")


# -------------------------------------------------------------------------------


class QueryNoRoutingRule(BaseRoutingRule):
    name = "QUERY_NO"

    @classmethod
    def build_request_option(cls, container_nos: List) -> RequestOption:
        url = f"{BASE_URL}/main_left_bottom.asp?KeyType=3&QueryNo={container_nos[0]}"

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=url,
            meta={
                "container_nos": container_nos,
            },
        )

    def get_save_name(self, response) -> str:
        return f"{self.name}.json"

    def handle(self, response):
        container_nos = response.meta["container_nos"]

        onclick = response.css("div#divx ::attr('onclick')").get()

        if not onclick:
            yield ExportErrorData(
                container_no=container_nos[0],
                detail="Data was not found",
                status=TERMINAL_RESULT_STATUS_ERROR,
            )
            return

        m = re.search(r"mainRight\(0,(?P<query_no>\d+)\)", onclick)
        query_no = m.group("query_no")

        yield ContainerRoutingRule.build_request_option(container_nos=container_nos, query_no=query_no)


# -------------------------------------------------------------------------------


class ContainerRoutingRule(BaseRoutingRule):
    name = "CONTAINER"

    @classmethod
    def build_request_option(cls, container_nos, query_no) -> RequestOption:
        url = f"{BASE_URL}/main_right.asp?KeyType=3&QueryNo={query_no}"

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=url,
            meta={
                "container_nos": container_nos,
            },
        )

    def get_save_name(self, response) -> str:
        return f"{self.name}.json"

    def handle(self, response):
        container_nos = response.meta["container_nos"]

        tables = response.css("table[style]")

        mbl_table_selector = tables[0]

        mbl_table_locator = GeneralTableLocator()
        mbl_table_locator.parse(table=mbl_table_selector)
        mbl_table = TableExtractor(table_locator=mbl_table_locator)

        container_table_selector = tables[1]

        container_table_locator = GeneralTableLocator()
        container_table_locator.parse(table=container_table_selector)
        container_table = TableExtractor(table_locator=container_table_locator)

        mbl_no = mbl_table.extract_cell("Master B/L")
        last_free_day = container_table.extract_cell("Last Free Date")
        gate_out_date = container_table.extract_cell("G.O.Date")

        yield TerminalItem(
            container_no=container_nos[0],
            mbl_no=mbl_no,
            last_free_day=last_free_day,
            gate_out_date=gate_out_date,
        )
        yield NextRoundRoutingRule.build_request_option(container_nos=container_nos)


# -------------------------------------------------------------------------------


class NextRoundRoutingRule(BaseRoutingRule):
    name = "NEXT_ROUND"

    @classmethod
    def build_request_option(cls, container_nos: List) -> RequestOption:
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url="https://eval.edi.hardcoretech.co/c/livez",
            meta={
                "container_nos": container_nos,
            },
        )

    def handle(self, response):
        container_nos = response.meta["container_nos"]

        if len(container_nos) <= MAX_PAGE_NUM:
            return

        container_nos = container_nos[MAX_PAGE_NUM:]

        yield QueryNoRoutingRule.build_request_option(container_nos=container_nos)


class GeneralTableLocator(BaseTable):
    def parse(self, table: Selector):
        title_ths = table.css("th")
        data_tds = table.css("td")

        for title_th, data_td in zip(title_ths, data_tds):
            title = title_th.css("::text").get().strip()

            self.add_left_header_set(title)
            td_dict = self._td_map.setdefault(title, {})
            td_dict[0] = data_td
