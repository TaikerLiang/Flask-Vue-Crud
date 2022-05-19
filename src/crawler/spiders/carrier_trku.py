import dataclasses
from typing import List

import scrapy
from scrapy import Selector

from crawler.core.base_new import (
    DUMMY_URL_DICT,
    RESULT_STATUS_ERROR,
    SEARCH_TYPE_BOOKING,
    SEARCH_TYPE_MBL,
)
from crawler.core.exceptions_new import SuspiciousOperationError
from crawler.core.items_new import DataNotFoundItem, EndItem
from crawler.core.table import BaseTable, TableExtractor
from crawler.core_carrier.base_spiders_new import BaseMultiCarrierSpider
from crawler.core_carrier.items_new import (
    BaseCarrierItem,
    ContainerItem,
    ContainerStatusItem,
    DebugItem,
    LocationItem,
    MblItem,
    VesselItem,
)
from crawler.core_carrier.request_helpers_new import RequestOption
from crawler.core_carrier.rules import BaseRoutingRule, RuleManager

BASE_URL = "https://turkon.com/en/Container-Tracking.aspx"


@dataclasses.dataclass
class HiddenFormSpec:
    view_state: str
    view_state_generator: str


class CarrierTrkuSpider(BaseMultiCarrierSpider):
    name = "carrier_trku"
    base_url = None
    custom_settings = {
        **BaseMultiCarrierSpider.custom_settings,  # type: ignore
        "CONCURRENT_REQUESTS": "1",
    }

    def __init__(self, *args, **kwargs):
        super(CarrierTrkuSpider, self).__init__(*args, **kwargs)

        bill_rules = [
            MainPageRoutingRule(),
            MainRoutingRule(search_type=SEARCH_TYPE_MBL),
            NextRoundRoutingRule(),
        ]

        booking_rules = [
            MainPageRoutingRule(),
            MainRoutingRule(search_type=SEARCH_TYPE_BOOKING),
            NextRoundRoutingRule(),
        ]

        if self.search_type == SEARCH_TYPE_MBL:
            self._rule_manager = RuleManager(rules=bill_rules)
        elif self.search_type == SEARCH_TYPE_BOOKING:
            self._rule_manager = RuleManager(rules=booking_rules)

    def start(self):
        option = MainPageRoutingRule.build_request_option(
            search_nos=self.search_nos, task_ids=self.task_ids, search_type=self.search_type
        )
        yield self._build_request_by(option=option)

    def parse(self, response):
        yield DebugItem(info={"meta": dict(response.meta)})

        routing_rule = self._rule_manager.get_rule_by_response(response=response)

        save_name = routing_rule.get_save_name(response=response)
        self._saver.save(to=save_name, text=response.text)

        for result in routing_rule.handle(response=response):
            if isinstance(result, (BaseCarrierItem, DataNotFoundItem, EndItem)):
                yield result
            elif isinstance(result, RequestOption):
                yield self._build_request_by(option=result)
            else:
                raise RuntimeError()

    def _build_request_by(self, option: RequestOption):
        meta = {
            RuleManager.META_CARRIER_CORE_RULE_NAME: option.rule_name,
            **option.meta,
        }

        if option.method == RequestOption.METHOD_GET:
            return scrapy.Request(
                url=option.url,
                meta=meta,
                headers=option.headers,
                dont_filter=True,
            )
        elif option.method == RequestOption.METHOD_POST_FORM:
            return scrapy.FormRequest(
                url=option.url,
                formdata=option.form_data,
                meta=meta,
                dont_filter=True,
            )
        else:
            if meta.get("task_ids"):
                zip_list = list(zip(meta["task_ids"], meta["search_nos"]))
                raise SuspiciousOperationError(
                    task_id=meta["task_ids"][0],
                    search_type=self.search_type,
                    reason=f"Unexpected request method: `{option.method}`, on (task_id, search_no): {zip_list}",
                )
            else:
                raise SuspiciousOperationError(
                    task_id=meta["task_id"],
                    search_no=meta["search_no"],
                    search_type=self.search_type,
                    reason=f"Unexpected request method: `{option.method}`",
                )


class MainPageRoutingRule(BaseRoutingRule):
    name = "MAIN_PAGE"

    @classmethod
    def build_request_option(cls, search_nos: List, task_ids: List, search_type) -> RequestOption:

        headers = {
            "authority": "turkon.com",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
            "referer": "https://turkon.com/en/Container-Tracking.aspx",
        }

        return RequestOption(
            method=RequestOption.METHOD_GET,
            rule_name=cls.name,
            url=BASE_URL,
            headers=headers,
            meta={
                "task_ids": task_ids,
                "search_nos": search_nos,
            },
        )

    def get_save_name(self, response) -> str:
        return f"{self.name}.html"

    def handle(self, response):
        task_ids = response.meta["task_ids"]
        search_nos = response.meta["search_nos"]

        hidden_form_spec = self._extract_hidden_form(response=response)
        yield MainRoutingRule.build_request_option(
            task_ids=task_ids,
            search_nos=search_nos,
            hidden_form_spec=hidden_form_spec,
        )

    def _extract_hidden_form(self, response: scrapy.Selector) -> HiddenFormSpec:
        form_selector = response.css("form[action='./Container-Tracking.aspx']")
        view_state = form_selector.css("input#__VIEWSTATE::attr(value)").get()
        view_state_generator = form_selector.css("input#__VIEWSTATEGENERATOR::attr(value)").get()
        return HiddenFormSpec(
            view_state=view_state,
            view_state_generator=view_state_generator,
        )


class MainRoutingRule(BaseRoutingRule):
    name = "MAIN"

    def __init__(self, search_type):
        self._search_type = search_type

    @classmethod
    def build_request_option(cls, search_nos: List, task_ids: List, hidden_form_spec: HiddenFormSpec) -> RequestOption:
        form_data = {
            "__VIEWSTATE": hidden_form_spec.view_state,
            "__VIEWSTATEGENERATOR": hidden_form_spec.view_state_generator,
            "ctl00$ContentPlaceHolder1$f_con": search_nos[0],
            "ctl00$ContentPlaceHolder1$Button1": "Search",
        }
        headers = {
            "authority": "turkon.com",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
            "referer": "https://turkon.com/en/Container-Tracking.aspx",
        }

        return RequestOption(
            method=RequestOption.METHOD_POST_FORM,
            rule_name=cls.name,
            url=BASE_URL,
            form_data=form_data,
            headers=headers,
            meta={
                "task_ids": task_ids,
                "search_nos": search_nos,
                "hidden_form_spec": hidden_form_spec,
            },
        )

    def get_save_name(self, response) -> str:
        return f"{self.name}.html"

    def handle(self, response):
        task_ids = response.meta["task_ids"]
        search_nos = response.meta["search_nos"]

        if self._is_search_no_invalid(response):
            yield DataNotFoundItem(
                task_id=task_ids[0],
                search_no=search_nos[0],
                search_type=self._search_type,
                status=RESULT_STATUS_ERROR,
                detail="Data was not found",
            )
            return

        basic_info = self._extract_basic_info(response)
        yield MblItem(
            mbl_no=search_nos[0],
            task_id=task_ids[0],
            **basic_info,
        )

        vessel_info = self._extract_vessel_info(response)
        for vessel in vessel_info:
            yield VesselItem(
                task_id=task_ids[0],
                **vessel,
            )

        containers = self._extract_container_info(response)
        for container in containers:
            yield ContainerItem(
                container_key=container["container_no"],
                container_no=container["container_no"],
                task_id=task_ids[0],
            )
            for container_status in self._extract_container_status(container["status_table"]):
                yield ContainerStatusItem(
                    **container_status,
                    container_key=container["container_no"],
                    task_id=task_ids[0],
                )
        yield EndItem(task_id=task_ids[0])
        yield NextRoundRoutingRule.build_request_option(
            search_nos=search_nos, task_ids=task_ids, hidden_form_spec=response.meta["hidden_form_spec"]
        )

    def _is_search_no_invalid(self, response: Selector):
        if not response.css("div#panel2 table thead tr"):
            return True
        return False

    def _extract_basic_info(self, response: Selector):
        steps = response.css("div.stepwizard-step p.longname")

        time_dict = {}
        for step in steps:
            text = step.css("::text").getall()
            if len(text) > 1:
                title, time = text[0], text[1]
                time_dict[title] = time
        return {
            "atd": time_dict.get("Sailed"),
            "ata": time_dict.get("Arrived"),
        }

    def _extract_vessel_info(self, response: Selector):
        table_selectors = response.css("div#panel2 table")
        vessel_list = []

        # first
        table_locator = TopHeaderTableLocator()
        table_locator.parse(table=table_selectors[0])
        table_extractor = TableExtractor(table_locator=table_locator)
        etd, atd = None, None
        if table_extractor.has_header(top="DEPARTURE DATE"):
            atd = table_extractor.extract_cell(top="DEPARTURE DATE")
        if table_extractor.has_header(top="ESTIMATED DEPARTURE DATE"):
            etd = table_extractor.extract_cell(top="ESTIMATED DEPARTURE DATE")
        vessel_list.append(
            {
                "pol": table_extractor.extract_cell(top="POL"),
                "vessel_key": table_extractor.extract_cell(top="VESSEL NAME"),
                "vessel": table_extractor.extract_cell(top="VESSEL NAME"),
                "voyage": table_extractor.extract_cell(top="VOYAGE"),
                "atd": atd,
                "etd": etd,
            }
        )
        # last
        table_locator = TopHeaderTableLocator()
        table_locator.parse(table=table_selectors[-1])
        table_extractor = TableExtractor(table_locator=table_locator)
        eta, ata = None, None
        if table_extractor.has_header(top="ARRIVAL DATE"):
            eta = table_extractor.extract_cell(top="ARRIVAL DATE")
        if table_extractor.has_header(top="ESTIMATED ARRIVAL DATE"):
            ata = table_extractor.extract_cell(top="ESTIMATED ARRIVAL DATE")
        vessel_list.append(
            {
                "pod": table_extractor.extract_cell(top="POD"),
                "vessel_key": table_extractor.extract_cell(top="VESSEL NAME"),
                "vessel": table_extractor.extract_cell(top="VESSEL NAME"),
                "voyage": table_extractor.extract_cell(top="VOYAGE"),
                "eta": eta,
                "ata": ata,
            }
        )
        return vessel_list

    def _extract_container_info(self, response: Selector):
        tables_selector = response.css("div#panel4 table")
        table_locator = TopHeaderTableLocator()
        table_locator.parse(table=tables_selector)
        table_extractor = TableExtractor(table_locator=table_locator)
        containers = []
        for left in table_locator.iter_left_header():
            containers.append(
                {
                    "container_no": table_extractor.extract_cell(left=left, top="Container").strip(),
                    "status_table": table_locator.get_cell(left=left, top=table_locator.title_num - 1),
                }
            )
        return containers

    def _extract_container_status(self, status_table: Selector):
        table_locator = ContainerStatusTableLocator()
        table_locator.parse(table=status_table)
        table_extractor = TableExtractor(table_locator=table_locator)
        container_status_list = []

        for left in table_locator.iter_left_header():
            container_status_list.append(
                {
                    "description": table_extractor.extract_cell(left=left, top="EVENT").strip(),
                    "local_date_time": table_extractor.extract_cell(left=left, top="EVENTDATE").strip(),
                    "vessel": table_extractor.extract_cell(left=left, top="VESSEL NAME").strip(),
                    "location": LocationItem(name=table_extractor.extract_cell(left=left, top="LOCATION").strip()),
                }
            )

        return container_status_list


class NextRoundRoutingRule(BaseRoutingRule):
    @classmethod
    def build_request_option(cls, search_nos: List, task_ids: List, hidden_form_spec: HiddenFormSpec) -> RequestOption:
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=DUMMY_URL_DICT["eval_edi"],
            meta={"search_nos": search_nos, "task_ids": task_ids, "hidden_form_spec": hidden_form_spec},
        )

    def handle(self, response):
        task_ids = response.meta["task_ids"]
        search_nos = response.meta["search_nos"]
        hidden_form_spec = response.meta["hidden_form_spec"]

        if len(search_nos) <= 1 and len(task_ids) <= 1:
            return

        task_ids = task_ids[1:]
        search_nos = search_nos[1:]

        yield MainRoutingRule.build_request_option(
            search_nos=search_nos,
            task_ids=task_ids,
            hidden_form_spec=hidden_form_spec,
        )


# -----------------------------------------------------------------------------------------


class TopHeaderTableLocator(BaseTable):
    def __init__(self):
        super(TopHeaderTableLocator, self).__init__()
        self.title_num = 0

    def parse(self, table: Selector):
        title_th_list = table.css("thead th")
        tbody = table.css("tbody")
        data_tr_list = tbody.css("tr.koyu, tr.acik")
        self._left_header_set = set(range(len(data_tr_list)))
        self.title_num = len(title_th_list)

        for title_index, title_th in enumerate(title_th_list):
            data_index = title_index

            title = title_th.css("::text").get()
            if title:
                title = title.strip()
            else:
                title = title_index
            self._td_map[title] = []

            for data_tr in data_tr_list:
                data_td = data_tr.css("td")[data_index]

                self._td_map[title].append(data_td)


# -----------------------------------------------------------------------------------------


class ContainerStatusTableLocator(BaseTable):
    def parse(self, table: Selector):
        title_div = table.css("div[style^='display:inline-block;']")[0]
        title_list = title_div.css("div[style^='float:left;']::text").getall()
        data_list = table.css("div[style^='display:inline-block;']")[1:]
        self._left_header_set = set(range(len(data_list)))

        for index, title in enumerate(title_list):
            title = title.strip()
            self._td_map[title] = []

            for data in data_list:
                data_div = data.css("div[style^='display:inline-block;'] > div[style^='float:left;']")[index]

                self._td_map[title].append(data_div)
