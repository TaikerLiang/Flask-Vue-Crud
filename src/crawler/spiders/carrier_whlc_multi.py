import re
import time
from typing import Dict, List, Optional

import scrapy
from scrapy import Selector
from selenium.common.exceptions import (
    NoAlertPresentException,
    NoSuchElementException,
    TimeoutException,
    UnexpectedAlertPresentException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from urllib3.exceptions import ReadTimeoutError

from crawler.core.base_new import (
    DUMMY_URL_DICT,
    RESULT_STATUS_ERROR,
    SEARCH_TYPE_BOOKING,
    SEARCH_TYPE_MBL,
)
from crawler.core.description import DATA_NOT_FOUND_DESC, SUSPICIOUS_OPERATION_DESC
from crawler.core.exceptions_new import (
    FormatError,
    SuspiciousOperationError,
    TimeOutError,
)
from crawler.core.items_new import DataNotFoundItem, EndItem
from crawler.core.proxy import HydraproxyProxyManager
from crawler.core.selenium import ChromeContentGetter
from crawler.core_carrier.base_spiders import BaseMultiCarrierSpider
from crawler.core_carrier.items import (
    BaseCarrierItem,
    ContainerItem,
    ContainerStatusItem,
    DebugItem,
    LocationItem,
    MblItem,
    VesselItem,
)
from crawler.core_carrier.request_helpers import RequestOption
from crawler.core_carrier.rules import BaseRoutingRule, RequestOptionQueue, RuleManager
from crawler.extractors.selector_finder import BaseMatchRule, find_selector_from
from crawler.extractors.table_cell_extractors import BaseTableCellExtractor
from crawler.extractors.table_extractors import (
    BaseTableLocator,
    HeaderMismatchError,
    TableExtractor,
)
from crawler.services.captcha_service import GoogleRecaptchaV2Service

WHLC_BASE_URL = "https://www.wanhai.com/views/cargoTrack/CargoTrack.xhtml"
COOKIES_RETRY_LIMIT = 3


class CarrierWhlcSpider(BaseMultiCarrierSpider):
    name = "carrier_whlc_multi"
    custom_settings = {
        **BaseMultiCarrierSpider.custom_settings,  # type: ignore
        "CONCURRENT_REQUESTS": "1",
    }

    def __init__(self, *args, **kwargs):
        super(CarrierWhlcSpider, self).__init__(*args, **kwargs)

        self._content_getter = ContentGetter(
            HydraproxyProxyManager(session="whlc", logger=self.logger), is_headless=True
        )
        # self._content_getter = ContentGetter(None, is_headless=True)

        self._retry_count = 0
        bill_rules = [
            MblRoutingRule(content_getter=self._content_getter),
            NextRoundRoutingRule(search_type=self.search_type),
        ]
        booking_rules = [
            BookingRoutingRule(content_getter=self._content_getter),
            NextRoundRoutingRule(search_type=self.search_type),
        ]

        if self.search_type == SEARCH_TYPE_MBL:
            self._rule_manager = RuleManager(rules=bill_rules)
        elif self.search_type == SEARCH_TYPE_BOOKING:
            self._rule_manager = RuleManager(rules=booking_rules)

        self._request_queue = RequestOptionQueue()

    def start(self):
        if self.search_type == SEARCH_TYPE_MBL:
            request_option = MblRoutingRule.build_request_option(search_nos=self.search_nos, task_ids=self.task_ids)
            yield self._build_request_by(option=request_option)
        else:
            request_option = BookingRoutingRule.build_request_option(search_nos=self.search_nos, task_ids=self.task_ids)
            yield self._build_request_by(option=request_option)

    def parse(self, response):
        yield DebugItem(info={"meta": dict(response.meta)})

        routing_rule = self._rule_manager.get_rule_by_response(response=response)

        save_name = routing_rule.get_save_name(response=response)
        self._saver.save(to=save_name, text=response.text)

        for result in routing_rule.handle(response=response):
            if isinstance(result, (BaseCarrierItem, DataNotFoundItem, EndItem)):
                yield result
            elif isinstance(result, RequestOption):
                self._request_queue.add_request(result)
            else:
                pass

        if not self._request_queue.is_empty():
            request_option = self._request_queue.get_next_request()
            yield self._build_request_by(option=request_option)

    def _build_request_by(self, option: RequestOption):
        meta = {
            RuleManager.META_CARRIER_CORE_RULE_NAME: option.rule_name,
            **option.meta,
        }

        if option.method == RequestOption.METHOD_POST_BODY:
            return scrapy.Request(
                url=option.url,
                headers=option.headers,
                meta=meta,
                callback=self.parse,
                method="POST",
                body=option.body,
                dont_filter=True,
            )
        elif option.method == RequestOption.METHOD_GET:
            return scrapy.Request(
                method="GET",
                url=option.url,
                headers=option.headers,
                meta=meta,
                dont_filter=True,
            )
        else:
            zip_list = list(zip(meta["task_ids"], meta["search_nos"]))
            raise SuspiciousOperationError(
                task_id=meta["task_ids"][0],
                search_type=self.search_type,
                reason=SUSPICIOUS_OPERATION_DESC.format(method=option.method)
                + f", on (task_id, search_no): {zip_list}",
            )


# -------------------------------------------------------------------------------


class MblRoutingRule(BaseRoutingRule):
    name = "MBL_RULE"

    def __init__(self, content_getter):
        self._container_patt = re.compile(r"^(?P<container_no>\w+)")
        self._j_idt_patt = re.compile(r"'(?P<j_idt>j_idt[^,]+)':'(?P=j_idt)'")
        self._search_type = SEARCH_TYPE_MBL
        self._driver = content_getter

    @classmethod
    def build_request_option(cls, search_nos: List[str], task_ids: List[str]):
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=DUMMY_URL_DICT["eval_edi"],
            meta={"mbl_nos": search_nos, "task_ids": task_ids},
        )

    def handle(self, response):
        task_ids = response.meta["task_ids"][:1]
        mbl_nos = response.meta["mbl_nos"][:1]

        info_pack = {"task_id": task_ids[0], "search_no": mbl_nos[0], "search_type": self._search_type}

        try:
            self._driver.multi_search(search_nos=mbl_nos, search_type=self._search_type)
        except ReadTimeoutError:
            raise TimeOutError(**info_pack, reason="Timeout for multi search function")

        try:
            self._driver.check_alert()
            for mbl_no, task_id in zip(mbl_nos, task_ids):
                yield DataNotFoundItem(
                    task_id=task_id,
                    search_no=mbl_no,
                    search_type=self._search_type,
                    status=RESULT_STATUS_ERROR,
                    detail=DATA_NOT_FOUND_DESC,
                )
            return
        except (NoAlertPresentException, UnexpectedAlertPresentException):
            pass

        response_selector = Selector(text=self._driver.get_page_source())
        container_list = self.extract_container_info(response_selector, task_ids=task_ids, mbl_nos=mbl_nos)

        for item in self.handle_mbl_items(container_list=container_list, task_ids=task_ids, mbl_nos=mbl_nos):
            yield item

        for item in self.handle_container_items(container_list=container_list, task_ids=task_ids, mbl_nos=mbl_nos):
            yield item

        yield NextRoundRoutingRule.build_request_option(
            search_nos=response.meta["mbl_nos"], task_ids=response.meta["task_ids"]
        )

    def get_save_name(self, response) -> str:
        return f"{self.name}.html"

    def extract_container_info(self, response: scrapy.Selector, task_ids: List, mbl_nos: List) -> List:
        table_selector = response.css("table.tbl-list")[0]
        table_locator = ContainerListTableLocator()
        table_locator.parse(table=table_selector)
        table = TableExtractor(table_locator=table_locator)
        return_list = []
        for left in table_locator.iter_left_headers():
            container_no_text = table.extract_cell("Ctnr No.", left)
            container_no = self._parse_container_no_from(text=container_no_text, task_ids=task_ids, mbl_nos=mbl_nos)

            mbl_no_text = table.extract_cell("BL no.", left)
            mbl_no = self._parse_mbl_no_from(text=mbl_no_text, task_ids=task_ids, mbl_nos=mbl_nos)

            detail_j_idt_text = table.extract_cell("More detail", left, JidtTdExtractor())
            detail_j_idt = self._parse_detail_j_idt_from(text=detail_j_idt_text, task_ids=task_ids, mbl_nos=mbl_nos)

            history_j_idt_text = table.extract_cell("More History", left, JidtTdExtractor())
            history_j_idt = self._parse_history_j_idt_from(text=history_j_idt_text, task_ids=task_ids, mbl_nos=mbl_nos)

            return_list.append(
                {
                    "container_no": container_no,
                    "mbl_no": mbl_no,
                    "detail_j_idt": detail_j_idt,
                    "history_j_idt": history_j_idt,
                }
            )

        return return_list

    def handle_mbl_items(self, container_list: List, task_ids: List, mbl_nos: List):
        mbl_no_set = self._get_mbl_no_set_from(container_list=container_list)
        for mbl_no, task_id in zip(mbl_nos, task_ids):
            if mbl_no in mbl_no_set:
                yield MblItem(task_id=task_id, mbl_no=mbl_no)
            else:
                yield DataNotFoundItem(
                    task_id=task_id,
                    search_no=mbl_no,
                    search_type=self._search_type,
                    status=RESULT_STATUS_ERROR,
                    detail="Data was not found",
                )

    def handle_container_items(self, container_list: List, task_ids: List, mbl_nos: List):
        for idx in range(len(container_list)):
            container_no = container_list[idx]["container_no"]
            mbl_no = container_list[idx]["mbl_no"]
            index = mbl_nos.index(mbl_no)
            task_id = task_ids[index]

            info_pack = {"task_id": task_id, "search_no": mbl_no, "search_type": self._search_type}

            yield ContainerItem(
                task_id=task_id,
                container_key=container_no,
                container_no=container_no,
            )

            for item in self.handle_detail_page(idx=idx, info_pack=info_pack):
                yield item

            for item in self.handle_history_page(idx=idx, info_pack=info_pack, container_no=container_no):
                yield item

        if self._driver.get_num_of_tabs() > 1:
            self._driver.close()
            self._driver.switch_to_last()

    def handle_detail_page(self, idx: int, info_pack: Dict):
        try:
            self._driver.go_detail_page(idx + 2)
            detail_selector = Selector(text=self._driver.get_page_source())
            date_information = self._extract_date_information(detail_selector, info_pack=info_pack)

            yield VesselItem(
                task_id=info_pack["task_id"],
                vessel_key=f"{date_information['pol_vessel']} / {date_information['pol_voyage']}",
                vessel=date_information["pol_vessel"],
                voyage=date_information["pol_voyage"],
                pol=LocationItem(un_lo_code=date_information["pol_un_lo_code"]),
                etd=date_information["pol_etd"],
            )

            yield VesselItem(
                task_id=info_pack["task_id"],
                vessel_key=f"{date_information['pod_vessel']} / {date_information['pod_voyage']}",
                vessel=date_information["pod_vessel"],
                voyage=date_information["pod_voyage"],
                pod=LocationItem(un_lo_code=date_information["pod_un_lo_code"]),
                eta=date_information["pod_eta"],
            )

            if self._driver.get_num_of_tabs() > 2:
                self._driver.close()
                self._driver.switch_to_last()

        except TimeoutException:
            raise TimeOutError(**info_pack, reason="Timeout for search history page")
            self._driver.close()
            self._driver.switch_to_last()
        except NoSuchElementException:
            pass

    def handle_history_page(self, idx: int, info_pack: Dict, container_no: str):
        try:
            self._driver.go_history_page(idx + 2)
            history_selector = Selector(text=self._driver.get_page_source())
            container_status_list = self._extract_container_status(history_selector, info_pack=info_pack)

            for container_status in container_status_list:
                yield ContainerStatusItem(
                    task_id=info_pack["task_id"],
                    container_key=container_no,
                    local_date_time=container_status["local_date_time"],
                    description=container_status["description"],
                    location=LocationItem(name=container_status["location_name"]),
                )

            if self._driver.get_num_of_tabs() > 2:
                self._driver.close()
                self._driver.switch_to_last()

        except NoSuchElementException:
            pass
        except TimeoutException:
            raise TimeOutError(**info_pack, reason="Timeout for search history page")
            self._driver.close()
            self._driver.switch_to_last()

    def _parse_container_no_from(self, text: Optional[str], task_ids: List[str], mbl_nos: List[str]):
        if not text:
            zip_list = list(zip(task_ids, mbl_nos))
            raise FormatError(
                task_id=task_ids[0],
                search_type=self._search_type,
                reason=f"container_no not found, on (task_id, search_no): {zip_list}",
            )

        m = self._container_patt.match(text)
        if not m:
            zip_list = list(zip(task_ids, mbl_nos))
            raise FormatError(
                task_id=task_ids[0],
                search_type=self._search_type,
                reason=f"container_no not match, on (task_id, search_no): {zip_list}",
            )

        return m.group("container_no")

    def _parse_mbl_no_from(self, text: Optional[str], task_ids: List[str], mbl_nos: List[str]):
        if not text:
            zip_list = list(zip(task_ids, mbl_nos))
            raise FormatError(
                task_id=task_ids[0],
                search_type=self._search_type,
                reason=f"mbl_no not found, on (task_id, search_no): {zip_list}",
            )

        m = self._container_patt.match(text)
        if not m:
            zip_list = list(zip(task_ids, mbl_nos))
            raise FormatError(
                task_id=task_ids[0],
                search_type=self._search_type,
                reason=f"mbl_no not match, on (task_id, search_no): {zip_list}",
            )

        return m.group("container_no")

    def _parse_detail_j_idt_from(self, text: Optional[str], task_ids: List[str], mbl_nos: List[str]) -> str:
        if not text:
            return ""

        m = self._j_idt_patt.search(text)
        if not m:
            zip_list = list(zip(task_ids, mbl_nos))
            raise FormatError(
                task_id=task_ids[0],
                search_type=self._search_type,
                reason=f"detail_j_idt not match, on (task_id, search_no): {zip_list}",
            )

        return m.group("j_idt")

    def _parse_history_j_idt_from(self, text: Optional[str], task_ids: List[str], mbl_nos: List[str]) -> str:
        if not text:
            return ""

        m = self._j_idt_patt.search(text)
        if not m:
            zip_list = list(zip(task_ids, mbl_nos))
            raise FormatError(
                task_id=task_ids[0],
                search_type=self._search_type,
                reason=f"History_j_idt not match, on (task_id, search_no): {zip_list}",
            )

        return m.group("j_idt")

    def _extract_date_information(self, response, info_pack: Dict) -> Dict:
        pattern = re.compile(r"^(?P<vessel>[^/]+) / (?P<voyage>[^/]+)$")

        match_rule = NameOnTableMatchRule(name="2. Departure Date / Arrival Date Information")

        table_selector = find_selector_from(selectors=response.css("table.tbl-list"), rule=match_rule)

        if table_selector is None:
            raise FormatError(
                **info_pack,
                reason="data information table not found",
            )

        location_table_locator = LocationLeftTableLocator()
        location_table_locator.parse(table=table_selector)
        location_table = TableExtractor(table_locator=location_table_locator)

        date_table_locator = DateLeftTableLocator()
        date_table_locator.parse(table=table_selector)
        date_table = TableExtractor(table_locator=date_table_locator)

        un_lo_code_index = 0
        vessel_voyage_index = 1
        date_index = 0

        pol_vessel_voyage = location_table.extract_cell(top=vessel_voyage_index, left="Loading Port")
        pol_m = pattern.match(pol_vessel_voyage)
        pol_vessel = pol_m.group("vessel")
        pol_voyage = pol_m.group("voyage")

        pod_vessel_voyage = location_table.extract_cell(top=vessel_voyage_index, left="Discharging Port")
        pod_m = pattern.match(pod_vessel_voyage)
        pod_vessel = pod_m.group("vessel")
        pod_voyage = pod_m.group("voyage")

        return {
            "pol_un_lo_code": location_table.extract_cell(top=un_lo_code_index, left="Loading Port"),
            "pod_un_lo_code": location_table.extract_cell(top=un_lo_code_index, left="Discharging Port"),
            "pol_vessel": pol_vessel,
            "pol_voyage": pol_voyage,
            "pod_vessel": pod_vessel,
            "pod_voyage": pod_voyage,
            "pod_eta": date_table.extract_cell(top=date_index, left="Arrival Date"),
            "pol_etd": date_table.extract_cell(top=date_index, left="Departure Date"),
        }

    def _extract_container_status(self, response, info_pack: Dict) -> List:
        table_selector = response.css("table.tbl-list")

        if not table_selector:
            raise FormatError(
                **info_pack,
                reason="container status table not found",
            )

        table_locator = ContainerStatusTableLocator()
        table_locator.parse(table=table_selector)
        table = TableExtractor(table_locator=table_locator)

        return_list = []
        for left in table_locator.iter_left_headers():
            description = table.extract_cell(top="Status Name", left=left, extractor=DescriptionTdExtractor())
            local_date_time = table.extract_cell(top="Ctnr Date", left=left, extractor=LocalDateTimeTdExtractor())
            location_name = table.extract_cell(top="Ctnr Depot Name", left=left, extractor=LocationNameTdExtractor())

            return_list.append(
                {
                    "local_date_time": local_date_time,
                    "description": description,
                    "location_name": location_name,
                }
            )

        return return_list

    def _get_mbl_no_set_from(self, container_list: List):
        mbl_no_list = [container["mbl_no"] for container in container_list]
        mbl_no_set = set(mbl_no_list)

        return mbl_no_set


class BookingRoutingRule(BaseRoutingRule):
    name = "BOOKING"

    def __init__(self, content_getter):
        self._search_type = SEARCH_TYPE_BOOKING
        self._container_patt = re.compile(r"^(?P<container_no>\w+)")
        self._driver: Optional[ContentGetter] = None
        self._driver = content_getter

    @classmethod
    def build_request_option(cls, search_nos: List[str], task_ids: List[str]):
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=DUMMY_URL_DICT["eval_edi"],
            meta={
                "booking_nos": search_nos,
                "task_ids": task_ids,
            },
        )

    def get_save_name(self, response) -> str:
        return f"{self.name}.html"

    def handle(self, response):
        task_ids = response.meta["task_ids"][:1]
        booking_nos = response.meta["booking_nos"][:1]
        info_pack = {"task_id": task_ids[0], "search_no": booking_nos[0], "search_type": self._search_type}

        try:
            self._driver.multi_search(search_nos=booking_nos, search_type=self._search_type)
        except ReadTimeoutError:
            raise TimeOutError(**info_pack, reason="Timeout for multi search function")

        try:
            self._driver.check_alert()
            for booking_no, task_id in zip(booking_nos, task_ids):
                yield DataNotFoundItem(
                    task_id=task_id,
                    search_no=booking_no,
                    search_type=self._search_type,
                    status=RESULT_STATUS_ERROR,
                    detail=DataNotFoundItem,
                )
            return
        except (NoAlertPresentException, UnexpectedAlertPresentException):
            pass

        response_selector = Selector(text=self._driver.get_page_source())
        booking_list = self._extract_booking_list(response_selector, task_ids=task_ids, search_nos=booking_nos)

        for item in self.handle_booking_items(booking_list=booking_list, task_ids=task_ids, booking_nos=booking_nos):
            yield item

        yield NextRoundRoutingRule.build_request_option(
            search_nos=response.meta["booking_nos"], task_ids=response.meta["task_ids"]
        )

    def handle_booking_items(self, booking_list: List, task_ids: List, booking_nos: List):
        for b_idx in range(len(booking_list)):
            booking_no = booking_list[b_idx]["booking_no"]
            index = booking_nos.index(booking_no)
            task_id = task_ids[index]

            info_pack = {"task_id": task_id, "search_no": booking_list, "search_type": self._search_type}

            for item in self.handle_detail_page(idx=b_idx, info_pack=info_pack):
                yield item

        if self._driver.get_num_of_tabs() > 1:
            self._driver.close()
            self._driver.switch_to_last()

    def handle_detail_page(self, idx: int, info_pack: Dict):
        try:
            self._driver.go_detail_page(idx + 2)  # only one booking_no to click
        except TimeoutException:
            raise TimeOutError(**info_pack, reason="Timeout for search booking detail page")
            self._driver.close()
            self._driver.switch_to_last()
        except NoSuchElementException:
            pass

        basic_info = self._extract_basic_info(Selector(text=self._driver.get_page_source()))
        vessel_info = self._extract_vessel_info(Selector(text=self._driver.get_page_source()))

        yield MblItem(
            task_id=info_pack["task_id"],
            booking_no=info_pack["search_no"],
        )

        yield VesselItem(
            task_id=info_pack["task_id"],
            vessel_key=f"{basic_info['vessel']} / {basic_info['voyage']}",
            vessel=basic_info["vessel"],
            voyage=basic_info["voyage"],
            pol=LocationItem(name=vessel_info["pol"]),
            etd=vessel_info["etd"],
        )

        yield VesselItem(
            task_id=info_pack["task_id"],
            vessel_key=f"{basic_info['vessel']} / {basic_info['voyage']}",
            vessel=basic_info["vessel"],
            voyage=basic_info["voyage"],
            pod=LocationItem(name=vessel_info["pod"]),
            eta=vessel_info["eta"],
        )

        container_nos = self._extract_container_no_and_status_links(Selector(text=self._driver.get_page_source()))

        for item in self.handle_container_page(container_nos=container_nos, info_pack=info_pack):
            yield item

        if self._driver.get_num_of_tabs() > 2:
            self._driver.close()
            self._driver.switch_to_last()

    def handle_container_page(self, container_nos: List[str], info_pack: Dict):
        for idx in range(len(container_nos)):
            container_no = container_nos[idx]
            try:
                self._driver.go_booking_history_page(idx + 2)
            except TimeoutException:
                raise TimeOutError(**info_pack, reason="Timeout for search booking container page")
                self._driver.close()
                self._driver.switch_to_last()
            except NoSuchElementException:
                pass
            history_selector = Selector(text=self._driver.get_page_source())

            event_list = self._extract_container_status(response=history_selector, info_pack=info_pack)
            container_status_items = self._make_container_status_items(info_pack["task_id"], container_no, event_list)

            yield ContainerItem(
                task_id=info_pack["task_id"],
                container_key=container_no,
                container_no=container_no,
            )

            for item in container_status_items:
                yield item

            if self._driver.get_num_of_tabs() > 2:
                self._driver.close()
                self._driver.switch_to_last()

    def _extract_booking_list(self, response: scrapy.Selector, task_ids: List[str], search_nos: List[str]) -> List:
        table_selector = response.css("table.tbl-list")[0]
        table_locator = ContainerListTableLocator()
        table_locator.parse(table=table_selector)
        table = TableExtractor(table_locator=table_locator)
        return_list = []
        for left in table_locator.iter_left_headers():
            booking_no_text = table.extract_cell("Book No.", left)
            booking_no = self._parse_booking_no_from(text=booking_no_text, task_ids=task_ids, search_nos=search_nos)

            detail_j_idt_text = table.extract_cell("More detail", left, JidtTdExtractor())
            detail_j_idt = self._parse_detail_j_idt_from(
                text=detail_j_idt_text, task_ids=task_ids, search_nos=search_nos
            )

            return_list.append(
                {
                    "booking_no": booking_no,
                    "detail_j_idt": detail_j_idt,
                }
            )

        return return_list

    def _parse_booking_no_from(self, text: Optional[str], task_ids: List[str], search_nos: List[str]):
        if not text:
            zip_list = list(zip(task_ids, search_nos))
            raise FormatError(
                task_id=task_ids[0],
                search_type=self._search_type,
                reason=f"booking_no not found, on (task_id, search_no): {zip_list}",
            )

        booking_patt = re.compile(r"^(?P<booking_no>\w+)")
        m = booking_patt.match(text)
        if not m:
            zip_list = list(zip(task_ids, search_nos))
            raise FormatError(
                task_id=task_ids[0],
                search_type=self._search_type,
                reason=f"booking_no not match, on (task_id, search_no): {zip_list}",
            )

        return m.group("booking_no")

    def _parse_detail_j_idt_from(self, text: Optional[str], task_ids: List[str], search_nos: List[str]) -> str:
        if not text:
            return ""

        j_idt_patt = re.compile(r"'(?P<j_idt>j_idt[^,]+)':'(?P=j_idt)'")
        m = j_idt_patt.search(text)
        if not m:
            zip_list = list(zip(task_ids, search_nos))
            raise FormatError(
                task_id=task_ids[0],
                search_type=self._search_type,
                reason=f"detail_j_idt not match, on (task_id, search_no): {zip_list}",
            )

        return m.group("j_idt")

    def _get_book_no_set_from(self, booking_list: List):
        book_no_list = [booking["booking_no"] for booking in booking_list]
        book_no_set = set(book_no_list)
        return book_no_set

    def _extract_basic_info(self, response: scrapy.Selector):
        tables = response.css("table.tbl-list")
        table = tables[0]

        table_locator = BookingBasicTableLocator()
        table_locator.parse(table=table)

        return {
            "vessel": table_locator.get_cell("Vessel Name"),
            "voyage": table_locator.get_cell("Voyage"),
        }

    def _extract_vessel_info(self, response: scrapy.Selector):
        tables = response.css("table.tbl-list")
        table = tables[1]

        table_locator = BookingVesselTableLocator()
        table_locator.parse(table=table)

        return {
            "por": table_locator.get_cell("Place of Receipt").replace("\xa0", " "),
            "pol": table_locator.get_cell("Port of Loading").replace("\xa0", " "),
            "pod": table_locator.get_cell("Port of Discharge").replace("\xa0", " "),
            "place_of_deliv": table_locator.get_cell("Place of Delivery").replace("\xa0", " "),
            "eta": table_locator.get_cell("Estimated Departure Date"),
            "etd": table_locator.get_cell("Estimated Arrival Date"),
        }

    def _extract_container_no_and_status_links(self, response: scrapy.Selector) -> List:
        tables = response.css("table.tbl-list")
        table = tables[-1]

        table_locator = BookingContainerListTableLocator()
        table_locator.parse(table=table)

        return table_locator.get_container_no_list()

    def _make_container_status_items(self, task_id, container_no, event_list):
        container_statuses = []
        for container_status in event_list:
            container_statuses.append(
                ContainerStatusItem(
                    task_id=task_id,
                    container_key=container_no,
                    local_date_time=container_status["local_date_time"],
                    description=container_status["description"],
                    location=LocationItem(name=container_status["location_name"]),
                )
            )
        return container_statuses

    def _extract_container_status(self, response, info_pack: Dict) -> List:
        table_selector = response.css("table.tbl-list")

        if not table_selector:
            raise FormatError(**info_pack, reason="container status table not found")

        table_locator = ContainerStatusTableLocator()
        table_locator.parse(table=table_selector)
        table = TableExtractor(table_locator=table_locator)

        return_list = []
        for left in table_locator.iter_left_headers():
            description = table.extract_cell(top="Status Name", left=left, extractor=DescriptionTdExtractor())
            local_date_time = table.extract_cell(top="Ctnr Date", left=left, extractor=LocalDateTimeTdExtractor())
            location_name = table.extract_cell(top="Ctnr Depot Name", left=left, extractor=LocationNameTdExtractor())

            return_list.append(
                {
                    "local_date_time": local_date_time,
                    "description": description,
                    "location_name": location_name,
                }
            )

        return return_list


# -------------------------------------------------------------------------------


class NextRoundRoutingRule(BaseRoutingRule):
    name = "ROUTING"

    def __init__(self, search_type: str):
        self._search_type = search_type

    @classmethod
    def build_request_option(cls, search_nos: List[str], task_ids: List[str]) -> RequestOption:
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url="https://eval.edi.hardcoretech.co/c/livez",
            meta={"search_nos": search_nos, "task_ids": task_ids},
        )

    def handle(self, response):
        task_ids = response.meta["task_ids"]
        search_nos = response.meta["search_nos"]

        if len(search_nos) == 1 and len(task_ids) == 1:
            return

        task_ids = task_ids[1:]
        search_nos = search_nos[1:]
        if self._search_type == SEARCH_TYPE_BOOKING:
            yield BookingRoutingRule.build_request_option(search_nos=search_nos, task_ids=task_ids)
        else:
            yield MblRoutingRule.build_request_option(search_nos=search_nos, task_ids=task_ids)


class ContentGetter(ChromeContentGetter):
    def __init__(self, proxy_manager, is_headless: bool):
        super().__init__(proxy_manager=proxy_manager, is_headless=is_headless)

        self._type_select_text_map = {
            SEARCH_TYPE_MBL: "BL no.",
            SEARCH_TYPE_BOOKING: "Book No.",
        }

    def _pass_recaptcha(self):
        site_key = "6Ld38BkUAAAAAPATwit3FXvga1PI6iVTb6zgXw62"

        try:
            g_url = self.get_current_url()
            if self._driver.find_element_by_id("main-iframe").get_attribute("src"):
                self._driver.switch_to.frame(self._driver.find_element_by_id("main-iframe"))
                time.sleep(1)
                g_captcha_solver = GoogleRecaptchaV2Service()
                token = g_captcha_solver.solve(g_url, site_key)
                time.sleep(2)
                self.execute_script('onCaptchaFinished("{}");'.format(token))
                time.sleep(10)
                self._driver.switch_to.default_content()
                time.sleep(1)
                return
        except NoSuchElementException:
            return

    def search(self, search_no, search_type):
        self._driver.get(f"{WHLC_BASE_URL}/views/cargoTrack/CargoTrack.xhtml")
        select_text = self._type_select_text_map[search_type]
        WebDriverWait(self._driver, 30).until(ec.visibility_of_element_located((By.CSS_SELECTOR, "div#loader")))
        self._driver.find_element_by_xpath(f"//*[@id='cargoType']/option[text()='{select_text}']").click()
        time.sleep(1)
        input_ele = self._driver.find_element_by_xpath('//*[@id="q_ref_no1"]')
        input_ele.send_keys(search_no)
        time.sleep(3)
        WebDriverWait(self._driver, 30).until(ec.element_to_be_clickable((By.XPATH, "//*[@id='quick_ctnr_query']")))

        self._driver.find_element_by_xpath('//*[@id="quick_ctnr_query"]').click()
        time.sleep(10)
        self._driver.switch_to.window(self._driver.window_handles[-1])

    def multi_search(self, search_nos, search_type):
        self._driver.get(
            "https://www.wanhai.com/views/cargoTrack/CargoTrack.xhtml?file_num=65580&parent_id=64738&top_file_num=64735"
        )
        time.sleep(20)
        self._pass_recaptcha()
        WebDriverWait(self._driver, 30).until(
            ec.visibility_of_element_located((By.CSS_SELECTOR, "#cargoTrackListBean"))
        )
        select_text = self._type_select_text_map[search_type]
        self._driver.find_element_by_xpath(f"//*[@id='cargoType']/option[text()='{select_text}']").click()
        time.sleep(1)

        for i, search_no in enumerate(search_nos):
            input_ele = self._driver.find_element_by_xpath(f'//*[@id="q_ref_no{i+1}"]')
            input_ele.send_keys(search_no)
            time.sleep(0.5)
        time.sleep(3)
        self._driver.find_element_by_xpath('//*[@id="Query"]').click()
        time.sleep(20)
        self._driver.switch_to.window(self._driver.window_handles[-1])

    def close_alert(self):
        self._driver.switch_to.alert.accept()

    def go_detail_page(self, idx: int):
        WebDriverWait(self._driver, 30).until(
            ec.element_to_be_clickable((By.XPATH, f'//*[@id="cargoTrackListBean"]/table/tbody/tr[{idx}]/td[1]/u'))
        )
        self._driver.find_element_by_xpath(f'//*[@id="cargoTrackListBean"]/table/tbody/tr[{idx}]/td[1]/u').click()
        time.sleep(1)
        self._driver.switch_to.window(self._driver.window_handles[-1])
        self._pass_recaptcha()
        WebDriverWait(self._driver, 30).until(ec.visibility_of_element_located((By.CSS_SELECTOR, "table.tbl-list")))

    def go_history_page(self, idx: int):
        self._driver.find_element_by_xpath(f'//*[@id="cargoTrackListBean"]/table/tbody/tr[{idx}]/td[11]/u').click()
        time.sleep(2)
        self._driver.switch_to.window(self._driver.window_handles[-1])
        self._pass_recaptcha()
        WebDriverWait(self._driver, 30).until(ec.visibility_of_element_located((By.CSS_SELECTOR, "table.tbl-list")))

    def go_booking_history_page(self, idx: int):
        # '/html/body/div[2]/div[1]/div/form/table[5]/tbody/tr[2]/td[2]/a'
        self._driver.find_element_by_xpath(
            f"/html/body/div[2]/div[1]/div/form/table[5]/tbody/tr[{idx}]/td[2]/a"
        ).click()
        time.sleep(2)
        self._driver.switch_to.window(self._driver.window_handles[-1])
        WebDriverWait(self._driver, 30).until(ec.visibility_of_element_located((By.CSS_SELECTOR, "table.tbl-list")))

    def switch_to_last(self):
        self._driver.switch_to.window(self._driver.window_handles[-1])
        time.sleep(1)

    @staticmethod
    def _transformat_to_dict(cookies: List[Dict]) -> Dict:
        return_cookies = {}
        for d in cookies:
            return_cookies[d["name"]] = d["value"]

        return return_cookies


class BookingBasicTableLocator(BaseTableLocator):
    def __init__(self):
        self._td_map = {}

    def parse(self, table: Selector, numbers: int = 1):
        tr_list = table.css("tbody tr")

        for tr in tr_list:
            # the value will be emtpy
            titles = tr.css("th")
            values = tr.css("td")

            for i in range(len(titles)):
                title = titles[i].css("strong::text").get().strip()
                value = (values[i].css("::text").get() or "").strip()
                self._td_map[title] = value

    def get_cell(self, top, left=None) -> Selector:
        return self._td_map[top]

    def has_header(self, top=None, left=None) -> bool:
        pass


class BookingVesselTableLocator(BaseTableLocator):
    def __init__(self):
        self._td_map = {}

    def parse(self, table: Selector, numbers: int = 1):
        tr_list = table.css("tbody tr")

        for tr in tr_list:
            # the value will be emtpy
            titles = tr.css("th")
            values = tr.css("td")

            for i in range(len(titles)):
                title = titles[i].css("strong::text").get().strip()
                value = (values[i].css("::text").get() or "").strip()
                self._td_map[title] = value

    def get_cell(self, top, left=None) -> Selector:
        return self._td_map[top]

    def has_header(self, top=None, left=None) -> bool:
        pass


class BookingContainerListTableLocator(BaseTableLocator):

    TR_TITLE_INDEX = 0
    TR_DATA_BEGIN_INDEX = 1

    def __init__(self):
        self._td_map = []
        self._data_len = 0

    def parse(self, table: Selector):
        title_tr = table.css("tbody tr")[self.TR_TITLE_INDEX]
        data_tr_list = table.css("tbody tr")[self.TR_DATA_BEGIN_INDEX :]

        title_text_list = title_tr.css("th strong::text").getall()
        title_text_list[0] = "ID"

        for data_tr in data_tr_list:
            if len(data_tr.css("td")) == 1:
                break
            row = {}
            for title_index, title_text in enumerate(title_text_list):
                title_text = title_text.strip()
                container_no = data_tr.css("td a::text").get().strip()
                tds = data_tr.css("td")
                row[title_text] = (tds[title_index].css("::text").get() or "").strip()
                if title_text == "Ctnr No.":
                    row[title_text] = container_no

            self._td_map.append(row)

    def get_container_no_list(self) -> List:
        return [row["Ctnr No."] for row in self._td_map]

    def get_cell(self, top, left) -> scrapy.Selector:
        try:
            return self._td_map[top][left]
        except KeyError as err:
            raise HeaderMismatchError(repr(err))

    def has_header(self, top=None, left=None) -> bool:
        return (top in self._td_map) and (left is None)

    def iter_left_headers(self):
        for index in range(self._data_len):
            yield index


class ContainerListTableLocator(BaseTableLocator):
    TR_TITLE_INDEX = 0
    TR_DATA_BEGIN_INDEX = 1

    def __init__(self):
        self._td_map = {}
        self._data_len = 0

    def parse(self, table: Selector):
        title_tr = table.css("tr")[self.TR_TITLE_INDEX]
        data_tr_list = table.css("tr")[self.TR_DATA_BEGIN_INDEX :]

        title_text_list = title_tr.css("th::text").getall()
        for title_index, title_text in enumerate(title_text_list):
            data_index = title_index

            title_text = title_text.strip()
            self._td_map[title_text] = []

            for data_tr in data_tr_list:
                data_td = data_tr.css("td")[data_index]

                self._td_map[title_text].append(data_td)

        first_title_text = title_text_list[0]
        self._data_len = len(self._td_map[first_title_text])

    def get_cell(self, top, left) -> scrapy.Selector:
        try:
            return self._td_map[top][left]
        except KeyError as err:
            raise HeaderMismatchError(repr(err))

    def has_header(self, top=None, left=None) -> bool:
        return (top in self._td_map) and (left is None)

    def iter_left_headers(self):
        for index in range(self._data_len):
            yield index


class LocationLeftTableLocator(BaseTableLocator):
    """
    +------------------------------------------------+ <tbody>
    | Title 1 | Data 1  | Data 2 | Title    | Data   | <tr>
    +---------+---------+--------+----------+--------+
    | Title 2 |         |        | Title    | Data   | <tr>
    +---------+---------+--------+----------+--------+ </tbody>
    (       only use here        )
    """

    TR_TITLE_INDEX_BEGIN = 1
    TH_TITLE_INDEX = 0
    TD_DATA_INDEX_BEGIN = 0
    TD_DATA_INDEX_END = 2

    def __init__(self):
        self._td_map = {}
        self._left_header_set = set()

    def parse(self, table: Selector):
        top_index_set = set()
        tr_list = table.css("tr")[self.TR_TITLE_INDEX_BEGIN :]

        for tr in tr_list:
            left_header = tr.css("th::text")[self.TH_TITLE_INDEX].get().strip()
            self._left_header_set.add(left_header)

            data_td_list = tr.css("td")[self.TD_DATA_INDEX_BEGIN : self.TD_DATA_INDEX_END]
            for top_index, td in enumerate(data_td_list):
                top_index_set.add(top_index)
                td_dict = self._td_map.setdefault(top_index, {})
                td_dict[left_header] = td

    def get_cell(self, top, left) -> Selector:
        try:
            return self._td_map[top][left]
        except KeyError as err:
            raise HeaderMismatchError(repr(err))

    def has_header(self, top=None, left=None) -> bool:
        return (top is None) and (left in self._left_header_set)


class DateLeftTableLocator(BaseTableLocator):
    """
    +------------------------------------------------+ <tbody>
    | Title   | Data    | Data   | Title 1  | Data   | <tr>
    +---------+---------+--------+----------+--------+
    | Title   |         |        | Title 2  | Data   | <tr>
    +---------+---------+--------+----------+--------+ </tbody>
                                 (   only use here   )
    """

    TR_TITLE_INDEX_BEGIN = 1
    TH_TITLE_INDEX = 1
    TD_DATA_INDEX_BEGIN = 2
    TD_DATA_INDEX_END = 3

    def __init__(self):
        self._td_map = {}
        self._left_header_set = set()

    def parse(self, table: Selector):
        top_index_set = set()
        tr_list = table.css("tr")[self.TR_TITLE_INDEX_BEGIN :]

        for tr in tr_list:
            left_header = tr.css("th::text")[self.TH_TITLE_INDEX].get().strip()
            self._left_header_set.add(left_header)

            data_td_list = tr.css("td")[self.TD_DATA_INDEX_BEGIN : self.TD_DATA_INDEX_END]
            for top_index, td in enumerate(data_td_list):
                top_index_set.add(top_index)
                td_dict = self._td_map.setdefault(top_index, {})
                td_dict[left_header] = td

    def get_cell(self, top, left) -> Selector:
        try:
            return self._td_map[top][left]
        except KeyError as err:
            raise HeaderMismatchError(repr(err))

    def has_header(self, top=None, left=None) -> bool:
        return (top is None) and (left in self._left_header_set)


class ContainerStatusTableLocator(BaseTableLocator):
    """
    +-----------------------------------+ <tbody>
    | Title 1 | Title 2 | ... | Title N | <tr>
    +---------+---------+-----+---------+
    | Data    |         |     |         | <tr>
    +---------+---------+-----+---------+
    | Data    |         |     |         | <tr>
    +---------+---------+-----+---------+
    | ...     |         |     |         | <tr>
    +---------+---------+-----+---------+
    | Data    |         |     |         | <tr>
    +---------+---------+-----+---------+ </tbody>
    """

    TR_TITLE_INDEX = 0
    TR_DATA_BEGIN_INDEX = 1

    def __init__(self):
        self._td_map = {}
        self._data_len = 0

    def parse(self, table: Selector):
        title_tr = table.css("tr")[self.TR_TITLE_INDEX]
        data_tr_list = table.css("tr")[self.TR_DATA_BEGIN_INDEX :]

        title_text_list = title_tr.css("th::text").getall()

        for title_index, title_text in enumerate(title_text_list):
            data_index = title_index

            title_text = title_text.strip()
            self._td_map[title_text] = []

            for data_tr in data_tr_list:
                data_td = data_tr.css("td")[data_index]

                self._td_map[title_text].append(data_td)

        self._data_len = len(data_tr_list)

    def get_cell(self, top, left) -> Selector:
        try:
            return self._td_map[top][left]
        except KeyError as err:
            raise HeaderMismatchError(repr(err))

    def has_header(self, top=None, left=None) -> bool:
        return (top in self._td_map) and (left is None)

    def iter_left_headers(self):
        for index in range(self._data_len):
            yield index


class DescriptionTdExtractor(BaseTableCellExtractor):
    def extract(self, cell: Selector) -> str:
        td_text = cell.css("::text").get()
        td_text = td_text.replace("\\n", "")
        td_text = " ".join(td_text.split())
        return td_text.strip()


class LocalDateTimeTdExtractor(BaseTableCellExtractor):
    def extract(self, cell: Selector) -> str:
        td_text = cell.css("::text").get()
        td_text = td_text.replace("\\n", "")
        return td_text.strip()


class LocationNameTdExtractor(BaseTableCellExtractor):
    def extract(self, cell: Selector) -> str:
        td_text = cell.css("::text").get()
        td_text = td_text.replace("\\n", "")
        td_text = td_text.replace("\\t", "")
        return td_text.strip()


class NameOnTableMatchRule(BaseMatchRule):
    TABLE_NAME_QUERY = "tr td a::text"

    def __init__(self, name: str):
        self.name = name

    def check(self, selector: scrapy.Selector) -> bool:
        table_name = selector.css(self.TABLE_NAME_QUERY).get()

        if not isinstance(table_name, str):
            return False

        return table_name.strip() == self.name


class JidtTdExtractor(BaseTableCellExtractor):
    def extract(self, cell: Selector):
        j_idt_text = cell.css("u a::attr(onclick)").get()
        return j_idt_text
