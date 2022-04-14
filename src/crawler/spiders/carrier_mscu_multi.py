import dataclasses
import re
from typing import Dict, List

import scrapy

from crawler.core.base_new import (
    DUMMY_URL_DICT,
    RESULT_STATUS_ERROR,
    SEARCH_TYPE_BOOKING,
    SEARCH_TYPE_MBL,
)
from crawler.core.description import (
    DATA_NOT_FOUND_DESC,
    MAX_RETRY_DESC,
    SUSPICIOUS_OPERATION_DESC,
)
from crawler.core.exceptions_new import (
    FormatError,
    MaxRetryError,
    SuspiciousOperationError,
)
from crawler.core.items_new import DataNotFoundItem, EndItem
from crawler.core.proxy_new import HydraproxyProxyManager
from crawler.core.table import BaseTable, TableExtractor
from crawler.core_carrier.base_spiders_new import BaseMultiCarrierSpider
from crawler.core_carrier.items_new import (
    BaseCarrierItem,
    ContainerItem,
    ContainerStatusItem,
    DebugItem,
    LocationItem,
    MblItem,
)
from crawler.core_carrier.request_helpers_new import RequestOption
from crawler.core_carrier.rules import BaseRoutingRule, RuleManager

URL = "https://www.msc.com"
MAX_RETRY_COUNT = 3


@dataclasses.dataclass
class Restart:
    search_nos: list
    task_ids: list
    reason: str = ""


class CarrierMscuSpider(BaseMultiCarrierSpider):
    name = "carrier_mscu_multi"
    custom_settings = {
        **BaseMultiCarrierSpider.custom_settings,  # type: ignore
        "CONCURRENT_REQUESTS": "1",
    }

    def __init__(self, *args, **kwargs):
        super(CarrierMscuSpider, self).__init__(*args, **kwargs)

        self._retry_count = 0

        bill_rules = [
            HomePageRoutingRule(search_type=SEARCH_TYPE_MBL),
            MainRoutingRule(search_type=SEARCH_TYPE_MBL),
            NextRoundRoutingRule(),
        ]

        booking_rules = [
            HomePageRoutingRule(search_type=SEARCH_TYPE_BOOKING),
            MainRoutingRule(search_type=SEARCH_TYPE_BOOKING),
            NextRoundRoutingRule(),
        ]

        if self.search_type == SEARCH_TYPE_MBL:
            self._rule_manager = RuleManager(rules=bill_rules)
        elif self.search_type == SEARCH_TYPE_BOOKING:
            self._rule_manager = RuleManager(rules=booking_rules)

        self._proxy_manager = HydraproxyProxyManager(session="mscu", logger=self.logger)

    def start(self):
        option = self._prepare_start(search_nos=self.search_nos, task_ids=self.task_ids)
        yield self._build_request_by(option=option)

    def _prepare_start(self, search_nos: List, task_ids: List):
        self._proxy_manager.renew_proxy()
        option = HomePageRoutingRule.build_request_option(search_nos=search_nos, task_ids=task_ids)
        proxy_option = self._proxy_manager.apply_proxy_to_request_option(option=option)
        return proxy_option

    def _prepare_restart(self, search_nos: List, task_ids: List, reason: str):
        if self._retry_count >= MAX_RETRY_COUNT:
            self._retry_count = 0
            option = NextRoundRoutingRule.build_request_option(search_nos=search_nos, task_ids=task_ids)
            return self._proxy_manager.apply_proxy_to_request_option(option)
        else:
            self._retry_count += 1
            self.logger.warning(f"----- {reason}, try new proxy and restart")
            return self._prepare_start(search_nos=search_nos, task_ids=task_ids)

    def parse(self, response):
        yield DebugItem(info={"meta": dict(response.meta)})

        routing_rule = self._rule_manager.get_rule_by_response(response=response)

        save_name = routing_rule.get_save_name(response=response)
        self._saver.save(to=save_name, text=response.text)

        for result in routing_rule.handle(response=response):
            if isinstance(result, (BaseCarrierItem, DataNotFoundItem, EndItem)):
                yield result
            elif isinstance(result, RequestOption):
                if result.rule_name == "NEXT_ROUND":
                    self._retry_count = 0

                proxy_option = self._proxy_manager.apply_proxy_to_request_option(result)
                yield self._build_request_by(option=proxy_option)
            elif isinstance(result, Restart):
                search_nos = result.search_nos
                task_ids = result.task_ids
                if self._retry_count >= MAX_RETRY_COUNT:
                    err = MaxRetryError(
                        task_id=task_ids[0],
                        search_no=search_nos[0],
                        search_type=self.search_type,
                        reason=MAX_RETRY_DESC.format(action="proxy", times=MAX_RETRY_COUNT),
                    )
                    yield err.build_error_data()
                option = self._prepare_restart(search_nos=search_nos, task_ids=task_ids, reason=result.reason)
                yield self._build_request_by(option=option)
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
            zip_list = list(zip(meta["task_ids"], meta["search_nos"]))
            raise SuspiciousOperationError(
                task_id=meta["task_ids"][0],
                reason=SUSPICIOUS_OPERATION_DESC.format(method=option.method)
                + f", on (task_id, search_no): {zip_list}",
            )


# -------------------------------------------------------------------------------


class HomePageRoutingRule(BaseRoutingRule):
    name = "HOME_PAGE"

    def __init__(self, search_type):
        self._search_type = search_type

    @classmethod
    def build_request_option(cls, search_nos: List, task_ids: List) -> RequestOption:
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url="https://www.msc.com/track-a-shipment?agencyPath=twn",
            meta={
                "search_nos": search_nos,
                "task_ids": task_ids,
            },
        )

    def get_save_name(self, response) -> str:
        return f"{self.name}.html"

    def handle(self, response):
        task_ids = response.meta["task_ids"]
        search_nos = response.meta["search_nos"]

        view_state = response.css("input#__VIEWSTATE::attr(value)").get()
        validation = response.css("input#__EVENTVALIDATION::attr(value)").get()

        yield MainRoutingRule.build_request_option(
            search_nos=search_nos,
            view_state=view_state,
            validation=validation,
            task_ids=task_ids,
            search_type=self._search_type,
        )


# -------------------------------------------------------------------------------


class MainRoutingRule(BaseRoutingRule):
    name = "MAIN"

    def __init__(self, search_type):
        self._search_type = search_type

    @classmethod
    def build_request_option(
        cls, search_nos: List, task_ids: List, view_state, validation, search_type
    ) -> RequestOption:
        drop_down_field = "containerbilloflading" if search_type == SEARCH_TYPE_MBL else "bookingnumber"
        form_data = {
            "__EVENTTARGET": "ctl00$ctl00$plcMain$plcMain$TrackSearch$hlkSearch",
            "__EVENTVALIDATION": validation,
            "__VIEWSTATE": view_state,
            "ctl00$ctl00$plcMain$plcMain$TrackSearch$txtBolSearch$TextField": search_nos[0],
            "ctl00$ctl00$plcMain$plcMain$TrackSearch$fldTrackingType$DropDownField": drop_down_field,
        }

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_POST_FORM,
            form_data=form_data,
            url="https://www.msc.com/track-a-shipment?agencyPath=twn",
            meta={
                "search_nos": search_nos,
                "task_ids": task_ids,
            },
        )

    def get_save_name(self, response) -> str:
        return f"{self.name}.html"

    def handle(self, response):
        task_ids = response.meta["task_ids"]
        search_nos = response.meta["search_nos"]
        info_pack = {
            "task_id": task_ids[0],
            "search_no": search_nos[0],
            "search_type": self._search_type,
        }

        if self._is_search_no_invalid(response=response):
            yield DataNotFoundItem(
                task_id=task_ids[0],
                search_type=self._search_type,
                search_no=search_nos[0],
                status=RESULT_STATUS_ERROR,
                detail=DATA_NOT_FOUND_DESC,
            )
            yield NextRoundRoutingRule.build_request_option(search_nos=search_nos, task_ids=task_ids)
            return

        extractor = Extractor(info_pack=info_pack)
        place_of_deliv_set = set()

        try:
            container_selector_map_list = extractor.locate_container_selector(response=response)
        except FormatError as e:
            yield DebugItem(info=repr(e))
            yield Restart(
                search_nos=search_nos,
                task_ids=task_ids,
                reason="format error when locating container_selector_map_list",
            )
            return

        for container_selector_map in container_selector_map_list:
            try:
                container_no = extractor.extract_container_no(container_selector_map)

                yield ContainerItem(
                    task_id=task_ids[0],
                    container_key=container_no,
                    container_no=container_no,
                )

                container_status_list = extractor.extract_container_status_list(container_selector_map)

                for container_status in container_status_list:
                    yield ContainerStatusItem(
                        task_id=task_ids[0],
                        container_key=container_no,
                        description=container_status["description"],
                        local_date_time=container_status["local_date_time"],
                        location=LocationItem(name=container_status["location"]),
                        vessel=container_status["vessel"] or None,
                        voyage=container_status["voyage"] or None,
                        est_or_actual=container_status["est_or_actual"],
                    )

                container_info = extractor.extract_container_info(container_selector_map)
                place_of_deliv_set.add(container_info["place_of_deliv"])

            except FormatError as e:
                yield e.build_error_data()

        if not place_of_deliv_set:
            place_of_deliv = None
        elif len(place_of_deliv_set) == 1:
            place_of_deliv = list(place_of_deliv_set)[0] or None
        else:
            yield FormatError(reason=f"Different place_of_deliv: `{place_of_deliv_set}`").build_error_data()
            yield NextRoundRoutingRule.build_request_option(search_nos=search_nos, task_ids=task_ids)
            return

        try:
            main_info = extractor.extract_main_info(response=response)
        except FormatError as e:
            yield DebugItem(info=repr(e))
            yield Restart(search_nos=search_nos, task_ids=task_ids, reason="format error when extracting main info")
            return

        latest_update = extractor.extract_latest_update(response=response)

        mbl_item = MblItem(
            task_id=task_ids[0],
            pol=LocationItem(name=main_info["pol"]),
            pod=LocationItem(name=main_info["pod"]),
            etd=main_info["etd"],
            eta=container_info["eta"],
            vessel=main_info["vessel"],
            place_of_deliv=LocationItem(name=place_of_deliv),
            latest_update=latest_update,
        )
        if self._search_type == SEARCH_TYPE_MBL:
            mbl_item["mbl_no"] = search_nos[0]
        else:
            mbl_item["booking_no"] = search_nos[0]
        yield mbl_item

        yield EndItem(task_id=task_ids[0])
        yield NextRoundRoutingRule.build_request_option(search_nos=search_nos, task_ids=task_ids)

    def _is_search_no_invalid(self, response: scrapy.Selector):
        error_message = response.css("div#ctl00_ctl00_plcMain_plcMain_pnlTrackingResults > h3::text").get()
        possible_prefix = ["Your reference number was not found", "We are unable to"]
        for prefix in possible_prefix:
            if error_message and prefix in error_message:
                return True
        return False


class NextRoundRoutingRule(BaseRoutingRule):
    name = "NEXT_ROUND"

    @classmethod
    def build_request_option(cls, search_nos: List, task_ids: List) -> RequestOption:
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=DUMMY_URL_DICT["eval_edi"],
            meta={
                "search_nos": search_nos,
                "task_ids": task_ids,
            },
        )

    def handle(self, response):
        task_ids = response.meta["task_ids"]
        search_nos = response.meta["search_nos"]

        if len(search_nos) == 1 and len(task_ids) == 1:
            return

        task_ids = task_ids[1:]
        search_nos = search_nos[1:]

        yield HomePageRoutingRule.build_request_option(search_nos=search_nos, task_ids=task_ids)


# -------------------------------------------------------------------------------


class Extractor:
    def __init__(self, info_pack: Dict):
        self._info_pack = info_pack
        self._mbl_no_pattern = re.compile(r"^Bill of lading: (?P<mbl_no>\S+) ([(]\d+ containers?[)])?$")
        self._container_no_pattern = re.compile(r"^Container: (?P<container_no>\S+)$")
        self._latest_update_pattern = re.compile(r"^Tracking results provided by MSC on (?P<latest_update>.+)$")

    def extract_main_info(self, response: scrapy.Selector):
        main_outer = response.css("div#ctl00_ctl00_plcMain_plcMain_rptBOL_ctl00_pnlBOLContent")
        error_message = (
            "Can not find main information frame by css `div#ctl00_ctl00_plcMain_plcMain_rptBOL_ctl00" "_pnlBOLContent`"
        )
        if not main_outer:
            raise FormatError(**self._info_pack, reason=error_message)

        table_selector = main_outer.xpath('./table[@class="resultTable singleRowTable"]')
        if not table_selector:
            return {
                "pol": None,
                "pod": None,
                "etd": None,
                "vessel": None,
            }

        table_locator = MainInfoTableLocator()
        table_locator.parse(table=table_selector)
        table_extractor = TableExtractor(table_locator=table_locator)

        return {
            "pol": table_extractor.extract_cell(top="Port of load"),
            "pod": table_extractor.extract_cell(top="Port of discharge"),
            "etd": table_extractor.extract_cell(top="Departure date"),
            "vessel": table_extractor.extract_cell(top="Vessel"),
        }

    def locate_container_selector(self, response) -> List[Dict]:
        container_content_list = response.css("dl.containerAccordion dd")
        map_list = []

        for container_content in container_content_list:
            container_no_bar = container_content.css("a.containerToggle")
            if not container_no_bar:
                raise FormatError(**self._info_pack, reason="Can not find container_no_bar !!!")

            container_stats_table = container_content.css("table.singleRowTable")

            if not container_stats_table:
                raise FormatError(**self._info_pack, reason="Can not find container_stats_table !!!")

            movements_table = container_content.css("table[class='resultTable']")
            if not movements_table:
                raise FormatError(**self._info_pack, reason="Can not find movements_table !!!")

            map_list.append(
                {
                    "container_no_bar": container_no_bar,
                    "container_stats_table": container_stats_table,
                    "movements_table": movements_table,
                }
            )

        return map_list

    def extract_container_no(self, container_selector_map: Dict[str, scrapy.Selector]):
        container_no_bar = container_selector_map["container_no_bar"]

        container_no_text = container_no_bar.css("::text").get()

        return self._parse_container_no(container_no_text)

    def extract_container_info(self, container_selector_map: Dict[str, scrapy.Selector]):
        table_selector = container_selector_map["container_stats_table"]

        table_locator = ContainerInfoTableLocator()
        table_locator.parse(table=table_selector)
        table_extractor = TableExtractor(table_locator=table_locator)

        return {
            "place_of_deliv": table_extractor.extract_cell(top="Shipped to"),
            "eta": table_extractor.extract_cell(top="Final POD ETA")
            if table_locator.has_header(top="Final POD ETA")
            else None,
        }

    def extract_container_status_list(self, container_selector_map: Dict[str, scrapy.Selector]):
        table_selector = container_selector_map["movements_table"]

        table_locator = ContainerStatusTableLocator()
        table_locator.parse(table=table_selector)
        table_extractor = TableExtractor(table_locator=table_locator)

        container_status_list = []
        for left in table_locator.iter_left_header():
            schedule_status = table_extractor.extract_cell(top=table_locator.STATUS_TOP, left=left)

            if schedule_status == "past":
                est_or_actual = "A"
            elif schedule_status == "future":
                est_or_actual = "E"
            else:
                raise FormatError(**self._info_pack, reason=f"Unknown schedule_status: `{schedule_status}`")

            container_status_list.append(
                {
                    "location": table_extractor.extract_cell(top="Location", left=left),
                    "local_date_time": table_extractor.extract_cell(top="Date", left=left),
                    "description": table_extractor.extract_cell(top="Description", left=left),
                    "vessel": table_extractor.extract_cell(top="Vessel", left=left),
                    "voyage": table_extractor.extract_cell(top="Voyage", left=left),
                    "est_or_actual": est_or_actual,
                }
            )

        return container_status_list

    def extract_latest_update(self, response: scrapy.Selector):
        latest_update_message = response.css("div#ctl00_ctl00_plcMain_plcMain_pnlTrackingResults > p::text").get()
        return self._parse_latest_update(latest_update_message)

    def _parse_container_no(self, container_no_text):
        """
        Sample Text:
            Container: GLDU7636572
        """
        m = self._container_no_pattern.match(container_no_text)

        if not m:
            raise FormatError(**self._info_pack, reason=f"Unknown container no format: `{container_no_text}`")

        return m.group("container_no")

    def _parse_latest_update(self, latest_update_message: str):
        """
        Sample Text:
            Tracking results provided by MSC on 05.11.2019 at 10:50 W. Europe Standard Time
        """
        m = self._latest_update_pattern.match(latest_update_message)
        if not m:
            raise FormatError(
                **self._info_pack, reason=f"Unknown latest update message format: `{latest_update_message}`"
            )

        return m.group("latest_update").strip()


class MainInfoTableLocator(BaseTable):
    """
    +-----------+-----------+-----+-----------+ <thead>      -+
    | Title A-1 | Title A-2 | ... | Title A-N | <tr> <th>     |
    +-----------+-----------+-----+-----------+ <tbody>       | A
    | Cell A-1  | Cell A-2  | ... | Cell A-N  | <tr> <td>     |
    +-----------+-----------+-----+-----------+ <thead>      -+
    | Title B-1 | Title B-2 | ... | Title B-N | <tr> <th>     |
    +-----------+-----------+-----+-----------+ <tbody>       | B
    | Cell B-1  | Cell B-2  | ... | Cell B-N  | <tr> <td>     |
    +-----------+-----------+-----+-----------+              -+
    """

    def parse(self, table: scrapy.Selector):
        title_th_list = table.css("thead tr th")
        title_text_list = [self._extract_top(th=th) for th in title_th_list]
        data_td_list = table.css("tbody tr td")

        for index, (title, data_td) in enumerate(zip(title_text_list, data_td_list)):
            self._left_header_set.add(index)
            self._td_map.setdefault(title, [])
            self._td_map[title].append(data_td)

    def _extract_top(self, th):
        th_text = th.css("::text").get()
        return th_text.strip() if isinstance(th_text, str) else ""


class ContainerInfoTableLocator(BaseTable):
    """
    +-----------+-----------+-----+-----------+ <thead>      -+
    | Title A-1 | Title A-2 | ... | Title A-N | <tr> <th>     |
    +-----------+-----------+-----+-----------+ <tbody>       | A
    | Cell A-1  | Cell A-2  | ... | Cell A-N  | <tr> <td>     |
    +-----------+-----------+-----+-----------+ <thead>      -+
    | Title B-1 | Title B-2 | ... | Title B-N | <tr> <th>     |
    +-----------+-----------+-----+-----------+ <tbody>       | B
    | Cell B-1  | Cell B-2  | ... | Cell B-N  | <tr> <td>     |
    +-----------+-----------+-----+-----------+              -+
    """

    def parse(self, table: scrapy.Selector):
        title_th_list = table.css("thead tr th")
        title_text_list = [self._extract_top(th=th) for th in title_th_list]
        data_td_list = table.css("tbody tr td")

        for index, (title, data_td) in enumerate(zip(title_text_list, data_td_list)):
            self._left_header_set.add(index)
            self._td_map.setdefault(title, [])
            self._td_map[title].append(data_td)

    def _extract_top(self, th):
        th_text = th.css("::text").get()
        return th_text.strip() if isinstance(th_text, str) else ""


class ContainerStatusTableLocator(BaseTable):
    STATUS_TOP = "STATUS"

    def parse(self, table: scrapy.Selector):
        title_th_list = table.css("thead th")
        title_text_list = [self._extract_top(th=th) for th in title_th_list]
        data_tr_list = table.css("tbody tr")

        for index, data_tr in enumerate(data_tr_list):
            status = data_tr.css("::attr(class)").get()
            status_td = scrapy.Selector(text=f"<td>{status}</td>")
            self._td_map.setdefault(self.STATUS_TOP, [])
            self._td_map[self.STATUS_TOP].append(status_td)

            data_td_list = data_tr.css("td")
            self._left_header_set.add(index)
            for title, data_td in zip(title_text_list, data_td_list):
                self._td_map.setdefault(title, [])
                self._td_map[title].append(data_td)

    def _extract_top(self, th):
        top_header = th.css("::text").get()
        return top_header.strip() if isinstance(top_header, str) else ""
