import re
from typing import Dict, List
from urllib.parse import urlencode

from scrapy import Request, Selector

from crawler.core.table import BaseTable, TableExtractor
from crawler.core_terminal.base import TERMINAL_RESULT_STATUS_ERROR
from crawler.core_terminal.base_spiders import BaseMultiTerminalSpider
from crawler.core_terminal.items import DebugItem, ExportErrorData, TerminalItem
from crawler.core_terminal.rules import BaseRoutingRule, RequestOption, RuleManager

MAX_PAGE_NUM = 20
SHIPMENT_TYPE_MBL = "MBL"
SHIPMENT_TYPE_CONTAINER = "CONTAINER"


class StgShareSpider(BaseMultiTerminalSpider):
    firms_code = ""
    name = ""
    custom_settings = {
        **BaseMultiTerminalSpider.custom_settings,  # type: ignore
        "CONCURRENT_REQUESTS": "1",
    }

    def __init__(self, *args, **kwargs):
        super(StgShareSpider, self).__init__(*args, **kwargs)

        # self.custom_settings.update({"CONCURRENT_REQUESTS": "1"})

        rules = [
            ContainerRoutingRule(),
            NextRoundRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)

    def start(self):
        unique_container_nos = list(self.cno_tid_map.keys())
        option = ContainerRoutingRule.build_request_option(
            search_nos=unique_container_nos, search_type=SHIPMENT_TYPE_CONTAINER
        )
        yield self._build_request_by(option=option)

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
            else:
                raise RuntimeError()

    def _build_request_by(self, option: RequestOption):
        meta = {
            RuleManager.META_TERMINAL_CORE_RULE_NAME: option.rule_name,
            **option.meta,
        }

        if option.method == RequestOption.METHOD_POST_BODY:
            return Request(
                method="POST",
                url=option.url,
                headers=option.headers,
                body=option.body,
                meta=meta,
                dont_filter=True,
            )
        elif option.method == RequestOption.METHOD_GET:
            return Request(
                method="GET",
                url=option.url,
                headers=option.headers,
                meta=meta,
                dont_filter=True,
            )
        else:
            raise ValueError(f"Invalid option.method [{option.method}]")


# -------------------------------------------------------------------------------


class ContainerRoutingRule(BaseRoutingRule):
    name = "CONTAINER"

    @classmethod
    def build_request_option(cls, search_nos, search_type) -> RequestOption:
        form_data = {
            "locationCode": "STGL" if search_type == SHIPMENT_TYPE_CONTAINER else "",
            "searchBy": "container" if search_type == SHIPMENT_TYPE_CONTAINER else "lineBl",
            "searchValue": search_nos[0],
        }

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_POST_BODY,
            url="https://cwportal.stgusa.com/warehousingSTG/warehousing?event=TRACKING_RUN",
            body=urlencode(form_data),
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_1_0) AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/87.0.4280.141 Safari/537.36"
                ),
            },
            meta={
                "search_nos": search_nos,
                "search_type": search_type,
            },
        )

    def get_save_name(self, response) -> str:
        return f"{self.name}.html"

    def handle(self, response):
        search_nos = response.meta["search_nos"]
        search_type = response.meta["search_type"]

        if self._is_container_no_invalid(response):
            yield ExportErrorData(
                container_no=search_nos[0],
                detail="Data was not found",
                status=TERMINAL_RESULT_STATUS_ERROR,
            )
            yield NextRoundRoutingRule.build_request_option(search_nos=search_nos)
            return

        if self._has_multiple_results(response):
            mbl_nos = self._extract_mbl_nos(response)
            yield ContainerRoutingRule.build_request_option(search_nos=mbl_nos, search_type=SHIPMENT_TYPE_MBL)
            yield NextRoundRoutingRule.build_request_option(search_nos=search_nos, search_type=SHIPMENT_TYPE_CONTAINER)
            return

        container_info = self._extract_container_info(response)
        self._extract_pickup_notes(response)

        appointment_date = f"{container_info['appointment_date']} {container_info['appointment_time']}".strip()
        yield TerminalItem(
            mbl_no=container_info["mbl_no"],
            container_no=container_info["container_no"],
            vessel=container_info["vessel"],
            available=container_info["available"],
            appointment_date=appointment_date,
        )
        yield NextRoundRoutingRule.build_request_option(search_nos=search_nos, search_type=search_type)

    def _is_container_no_invalid(self, response: Selector) -> bool:
        return bool(response.css("p.noResults"))

    def _has_multiple_results(self, response: Selector) -> bool:
        return bool(response.css("div#cmsWorkarea h3"))

    def _extract_mbl_nos(self, response: Selector) -> List:
        table_selector = response.css("table.spreadsheet")
        table_locator = CFSSearchResultTableLocator()
        table_locator.parse(table=table_selector)

        table = TableExtractor(table_locator=table_locator)

        mbl_nos = []
        for left in table_locator.iter_left_header():
            mbl_no = table.extract_cell(top="Master Bill", left=left)
            mbl_nos.append(mbl_no)
        return mbl_nos

    def _extract_container_info(self, response) -> Dict:
        left_table_selector = response.css("div.fl table")
        right_table_selector = response.css("div.fr table")

        left_table_locator = ContainerInfoTableLocator()
        right_table_locator = ContainerInfoTableLocator()

        left_table_locator.parse(table=left_table_selector)
        right_table_locator.parse(table=right_table_selector)

        left_table = TableExtractor(table_locator=left_table_locator)
        right_table = TableExtractor(table_locator=right_table_locator)

        return {
            "mbl_no": left_table.extract_cell(left="Master Bill Number"),
            "container_no": left_table.extract_cell(left="Container Number"),
            "vessel": left_table.extract_cell(left="Vessel Name"),
            "available": right_table.extract_cell(left="Status"),
            "appointment_date": right_table.extract_cell(left="Appointment Date"),
            "appointment_time": right_table.extract_cell(left="Appointment Time"),
        }

    def _extract_pickup_notes(self, response) -> Dict:
        table_selector = response.css("div.pickupNotes table")
        if not table_selector:
            return {}

        table_locator = PickupNotesTableLocator()
        table_locator.parse(table=table_selector)
        pickup_notes_table = TableExtractor(table_locator=table_locator)

        pickup_notes_data = pickup_notes_table.extract_cell(left="Pickup Notes")

        return {
            "last_free_day": self._parse_lfd(data=pickup_notes_data),
        }

    def _parse_lfd(self, data: str):
        pattern = re.compile(r"LFD (?P<lfd>\d+\-\d+)")
        m = pattern.search(data)

        if m:
            return m.group("lfd")


class NextRoundRoutingRule(BaseRoutingRule):
    name = "NEXT_ROUND"

    @classmethod
    def build_request_option(cls, search_nos: List, search_type: str) -> RequestOption:
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url="https://eval.edi.hardcoretech.co/c/livez",
            meta={
                "search_nos": search_nos,
                "search_type": search_type,
            },
        )

    def handle(self, response):
        search_nos = response.meta["search_nos"]
        search_type = response.meta["search_type"]

        if len(search_nos) == 1:
            return

        search_nos = search_nos[1:]

        yield ContainerRoutingRule.build_request_option(search_nos=search_nos, search_type=search_type)


class CFSSearchResultTableLocator(BaseTable):
    def parse(self, table: Selector):
        data_trs = table.css("tbody tr")
        titles = table.css("thead th::text").getall()

        for index, tr in enumerate(data_trs):
            data_tds = tr.css("td")
            self.add_left_header_set(index)
            for title, data_td in zip(titles, data_tds):
                self._td_map.setdefault(title, [])
                self._td_map[title].append(data_td)


class ContainerInfoTableLocator(BaseTable):
    def parse(self, table: Selector):
        tds = table.css("tr td")
        titles = [td.css("::text").get() for td in tds[::2]]
        data_tds = tds[1::2]

        for title, td in zip(titles, data_tds):
            if not title:
                break

            self.add_left_header_set(title)
            td_dict = self._td_map.setdefault(0, {})
            td_dict[title] = td


class PickupNotesTableLocator(BaseTable):
    def parse(self, table: Selector):
        tds = table.css("tr td")

        title = tds[0].css("::text").get()
        data_td = tds[1]

        self.add_left_header_set(title)
        td_dict = self._td_map.setdefault(0, {})
        td_dict[title] = data_td
