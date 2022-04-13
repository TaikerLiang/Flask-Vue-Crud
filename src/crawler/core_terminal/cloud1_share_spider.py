from typing import Dict

import scrapy
from scrapy import Selector

from crawler.core_terminal.base import (
    TERMINAL_RESULT_STATUS_ERROR,
    TERMINAL_RESULT_STATUS_FATAL,
)
from crawler.core_terminal.base_spiders import BaseMultiTerminalSpider
from crawler.core_terminal.exceptions import TerminalResponseFormatError
from crawler.core_terminal.items import DebugItem, ExportErrorData, TerminalItem
from crawler.core_terminal.request_helpers import RequestOption
from crawler.core_terminal.rules import BaseRoutingRule, RuleManager

BASE_URL = "https://cloud1.cargomanager.com/warehousing"


class Cloud1ShareSpider(BaseMultiTerminalSpider):
    firms_code = ""
    name = ""
    url_code = ""
    code = ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        rules = [
            ConfigureSettingsRule(),
            ContainerRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)

    def start(self):
        unique_container_nos = list(self.cno_tid_map.keys())
        for c_no in unique_container_nos:
            option = ConfigureSettingsRule.build_request_option(
                container_no=c_no, url_code=self.url_code, code=self.code
            )
            yield self._build_request_by(option=option)

    def parse(self, response):
        yield DebugItem(info={"meta": dict(response.meta)})

        routing_rule = self._rule_manager.get_rule_by_response(response=response)

        save_name = routing_rule.get_save_name(response=response)
        self._saver.save(to=save_name, text=response.text)

        for result in routing_rule.handle(response=response):
            if True in [isinstance(result, item) for item in [TerminalItem, ExportErrorData]]:
                c_no = result["container_no"]
                if c_no:
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
                method="GET",
                url=option.url,
                headers=option.headers,
                meta=meta,
                dont_filter=True,
            )
        elif option.method == RequestOption.METHOD_POST_FORM:
            return scrapy.FormRequest(
                url=option.url,
                headers=option.headers,
                formdata=option.form_data,
                meta=meta,
                dont_filter=True,
            )
        else:
            raise RuntimeError()


# -------------------------------------------------------------------------------


class ConfigureSettingsRule(BaseRoutingRule):
    name = "Configure"

    @classmethod
    def build_request_option(cls, container_no: str, url_code: str, code: str) -> RequestOption:
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_POST_FORM,
            url=f"{BASE_URL}{url_code}/availability/results.jsp",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            form_data={
                "code": code,
                "fileType": "CFS",
                "container": container_no,
                "MBL": "",
                "IT": "",
                "houseBL": "",
                "amsBlNo": "",
                "houseIT": "",
                "custRef": "",
                "entryNo": "",
                "trsackingNo": "",
            },
            meta={"container_no": container_no, "url_code": url_code},
        )

    def get_save_name(self, response) -> str:
        return f"{self.name}.html"

    def handle(self, response):
        container_no = response.meta["container_no"]

        if "No results found" in response.css("::text").getall():
            yield ExportErrorData(
                container_no=container_no,
                detail="Data was not found",
                status=TERMINAL_RESULT_STATUS_ERROR,
            )
        else:
            url_code = response.meta["url_code"]
            extra_url = response.css("script ::text").get().strip().split("'")[-2]

            yield ContainerRoutingRule.build_request_option(
                container_no=container_no, url=f"{BASE_URL}{url_code}/availability/{extra_url}"
            )


# -------------------------------------------------------------------------------


class ContainerRoutingRule(BaseRoutingRule):
    name = "Container"

    @classmethod
    def build_request_option(cls, container_no, url) -> RequestOption:
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=url,
            meta={"container_no": container_no},
        )

    def get_save_name(self, response) -> str:
        return f"{self.name}.html"

    def handle(self, response):
        container_no = response.meta["container_no"]
        info = Extractor.extract_table(response.css("table.cfsdetails"))

        if info["Container No:"] != container_no:
            yield ExportErrorData(
                container_no=container_no,
                status=TERMINAL_RESULT_STATUS_FATAL,
                detail="Target container_no does not meet the container_no that website shows",
            )
        else:
            yield TerminalItem(
                container_no=container_no,
                mbl_no=info["Master B/L No:"],
                available=info["Status:"],
                vessel=info["Vessel Name:"],
                last_free_day=info["Free Time Expires:"],
            )


# -------------------------------------------------------------------------------


class Extractor:
    def extract_table(table: Selector) -> Dict:
        info = {}

        for tr in table.css("tr")[1:]:
            tds = tr.css("td")

            if len(tds) != 4:
                raise TerminalResponseFormatError(reason="unexpected table format")

            for i in range(0, 4, 2):
                key = tds[i].css("::text").get()
                val = tds[i + 1].css("::text").get()

                if key:
                    info[key] = val if (val and val != "\xa0") else ""

        return info
