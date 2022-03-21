import asyncio
import dataclasses
import re
import time
from typing import Dict, List

import requests
import scrapy
from pyppeteer.dialog import Dialog
from pyppeteer.errors import NetworkError, PageError, TimeoutError
from scrapy import Request
from scrapy.http import TextResponse
from scrapy.selector.unified import Selector

from crawler.core.defines import BaseContentGetter
from crawler.core.proxy import HydraproxyProxyManager, ProxyManager
from crawler.core.pyppeteer import PyppeteerContentGetter
from crawler.core.table import BaseTable, TableExtractor
from crawler.core_carrier.base import (
    CARRIER_RESULT_STATUS_ERROR,
    SHIPMENT_TYPE_BOOKING,
    SHIPMENT_TYPE_MBL,
)
from crawler.core_carrier.base_spiders import BaseMultiCarrierSpider
from crawler.core_carrier.exceptions import (
    CarrierResponseFormatError,
    DriverMaxRetryError,
    SuspiciousOperationError,
)
from crawler.core_carrier.items import (
    BaseCarrierItem,
    ContainerItem,
    ContainerStatusItem,
    DebugItem,
    ExportErrorData,
    LocationItem,
    MblItem,
)
from crawler.core_carrier.request_helpers import RequestOption
from crawler.core_carrier.rules import BaseRoutingRule, RuleManager
from crawler.extractors.selector_finder import (
    BaseMatchRule,
    CssQueryExistMatchRule,
    CssQueryTextStartswithMatchRule,
    find_selector_from,
)
from crawler.extractors.table_cell_extractors import FirstTextTdExtractor

MAX_RETRY_COUNT = 10
EGLV_INFO_URL = "https://ct.shipmentlink.com/servlet/TDB1_CargoTracking.do"
EGLV_CAPTCHA_URL = "https://www.shipmentlink.com/servlet/TUF1_CaptchaUtils"


@dataclasses.dataclass
class Restart:
    search_nos: list
    task_ids: list
    reason: str = ""


class CarrierEglvSpider(BaseMultiCarrierSpider):
    name = "carrier_eglv_multi"

    def __init__(self, *args, **kwargs):
        super(CarrierEglvSpider, self).__init__(*args, **kwargs)
        self._retry_count = 0
        self.custom_settings.update({"CONCURRENT_REQUESTS": "1"})
        self._driver = EglvContentGetter(
            proxy_manager=HydraproxyProxyManager(session="eglv", logger=self.logger), is_headless=True
        )
        self._driver.patch_pyppeteer()

        bill_rules = [
            CargoTrackingRoutingRule(content_getter=self._driver, search_type=SHIPMENT_TYPE_MBL),
            NextRoundRoutingRule(),
        ]

        booking_rules = [
            CargoTrackingRoutingRule(content_getter=self._driver, search_type=SHIPMENT_TYPE_BOOKING),
            NextRoundRoutingRule(),
        ]

        if self.search_type == SHIPMENT_TYPE_MBL:
            self._rule_manager = RuleManager(rules=bill_rules)
        elif self.search_type == SHIPMENT_TYPE_BOOKING:
            self._rule_manager = RuleManager(rules=booking_rules)

    def start(self):
        option = CargoTrackingRoutingRule.build_request_option(search_nos=self.search_nos, task_ids=self.task_ids)
        yield self._build_request_by(option=option)

    def _prepare_restart(self, search_nos: List, task_ids: List):
        if self._retry_count >= MAX_RETRY_COUNT:
            raise DriverMaxRetryError()

        self._retry_count += 1
        self._driver.quit()
        time.sleep(3)
        self._driver = EglvContentGetter(
            proxy_manager=HydraproxyProxyManager(session="eglv", logger=self.logger), is_headless=True
        )
        self._driver.patch_pyppeteer()
        self._rule_manager.get_rule_by_name(CargoTrackingRoutingRule.name).driver = self._driver
        option = CargoTrackingRoutingRule.build_request_option(search_nos=search_nos, task_ids=task_ids)
        return self._build_request_by(option=option)

    def parse(self, response):
        yield DebugItem(info={"meta": dict(response.meta)})

        routing_rule = self._rule_manager.get_rule_by_response(response=response)

        if routing_rule.name != "CAPTCHA":
            save_name = routing_rule.get_save_name(response=response)
            self._saver.save(to=save_name, text=response.text)

        for result in routing_rule.handle(response=response):
            if isinstance(result, BaseCarrierItem):
                yield result
            elif isinstance(result, Restart):
                yield DebugItem(info=f"{result.reason}, Restarting...")
                yield self._prepare_restart(search_nos=result.search_nos, task_ids=result.task_ids)
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
                dont_filter=True,
            )
        elif option.method == RequestOption.METHOD_POST_FORM:
            return scrapy.FormRequest(
                url=option.url,
                formdata=option.form_data,
                dont_filter=True,
                meta=meta,
            )
        else:
            raise SuspiciousOperationError(msg=f"Unexpected request method: `{option.method}`")


# -------------------------------------------------------------------------------


class CargoTrackingRoutingRule(BaseRoutingRule):
    name = "CARGO_TRACKING"

    def __init__(self, content_getter: BaseContentGetter, search_type: str):
        self._search_type = search_type
        self.driver = content_getter

    @classmethod
    def build_request_option(cls, search_nos, task_ids):
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url="https://eval.edi.hardcoretech.co/c/livez",
            meta={
                "search_nos": search_nos,
                "task_ids": task_ids,
            },
        )

    def handle(self, response):
        search_nos = response.meta["search_nos"]
        task_ids = response.meta["task_ids"]

        try:
            page_source, is_exist = asyncio.get_event_loop().run_until_complete(
                self.driver.search_and_return(search_no=search_nos[0], search_type=self._search_type)
            )

            if not is_exist:
                yield ExportErrorData(
                    task_id=task_ids[0],
                    booking_no=search_nos[0],
                    status=CARRIER_RESULT_STATUS_ERROR,
                    detail="Data was not found",
                )
                yield NextRoundRoutingRule.build_request_option(search_nos=search_nos, task_ids=task_ids)
                return
        except (TimeoutError, NetworkError, PageError) as e:
            yield Restart(search_nos=search_nos, task_ids=task_ids, reason=str(e))
            return

        response = self.get_response_selector(
            url=EGLV_INFO_URL, httptext=page_source, meta={"search_nos": search_nos, "task_ids": task_ids}
        )

        if self._search_type == SHIPMENT_TYPE_MBL:
            rule = BillMainInfoRoutingRule(content_getter=self.driver)
        else:
            rule = BookingMainInfoRoutingRule(content_getter=self.driver)

        for result in rule.handle(response=response):
            yield result

    @staticmethod
    def get_response_selector(url, httptext, meta):
        return TextResponse(
            url=url,
            body=httptext,
            encoding="utf-8",
            request=Request(
                url=url,
                meta=meta,
            ),
        )

    @staticmethod
    def _is_mbl_no_invalid(response: Selector):
        return not bool(response.css('table[cellpadding="2"]'))


class MainInfoRoutingRule(BaseRoutingRule):
    def __init__(self, content_getter):
        self.content_getter = content_getter

    def get_save_name(self, response) -> str:
        return f"{self.name}.html"

    def handle_container_status(self, container_no, search_nos: List, task_ids: List):
        httptext = asyncio.get_event_loop().run_until_complete(self.content_getter.container_page(container_no))
        if httptext:
            response = self.get_response_selector(
                url=EGLV_INFO_URL, httptext=httptext, meta={"container_no": container_no, "task_id": task_ids[0]}
            )
            rule = ContainerStatusRoutingRule()

            for item in rule.handle(response):
                yield item

    @staticmethod
    def get_response_selector(url, httptext, meta):
        return TextResponse(
            url=url,
            body=httptext,
            encoding="utf-8",
            request=Request(
                url=url,
                meta=meta,
            ),
        )


class BillMainInfoRoutingRule(MainInfoRoutingRule):
    name = "MBL_MAIN_INFO"

    def __init__(self, content_getter):
        super().__init__(content_getter=content_getter)

    @classmethod
    def build_request_option(cls, search_nos: List, verification_code: str, task_ids: List) -> RequestOption:
        form_data = {
            "BL": search_nos[0],
            "CNTR": "",
            "bkno": "",
            "TYPE": "BL",
            "NO": [search_nos[0], "", "", "", "", ""],
            "SEL": "s_bl",
            # "captcha_input": verification_code,
            "hd_captcha_input": "",
        }

        return RequestOption(
            method=RequestOption.METHOD_POST_FORM,
            rule_name=cls.name,
            url=EGLV_INFO_URL,
            form_data=form_data,
            meta={
                "search_nos": search_nos,
                "task_ids": task_ids,
            },
        )

    def handle(self, response):
        for item in self._handle_main_info_page(response=response):
            yield item

    def _handle_main_info_page(self, response):
        task_ids = response.meta["task_ids"]
        search_nos = response.meta["search_nos"]

        mbl_no_info = self._extract_hidden_info(response=response)
        basic_info = self._extract_basic_info(response=response)
        vessel_info = self._extract_vessel_info(response=response, pod=basic_info["pod_name"])

        yield MblItem(
            task_id=task_ids[0],
            mbl_no=mbl_no_info["mbl_no"],
            vessel=vessel_info["vessel"],
            voyage=vessel_info["voyage"],
            por=LocationItem(name=basic_info["por_name"]),
            pol=LocationItem(name=basic_info["pol_name"]),
            pod=LocationItem(name=basic_info["pod_name"]),
            final_dest=LocationItem(name=basic_info["dest_name"]),
            place_of_deliv=LocationItem(name=basic_info["place_of_deliv_name"]),
            etd=basic_info["etd"],
            eta=vessel_info["eta"],
            cargo_cutoff_date=basic_info["cargo_cutoff_date"],
        )

        container_list = self._extract_container_info(response=response)
        for container in container_list:
            try:
                for item in self.handle_container_status(
                    container_no=container["container_no"], search_nos=search_nos, task_ids=task_ids
                ):
                    yield item
            except (TimeoutError, NetworkError, PageError) as e:
                yield Restart(search_nos=search_nos, task_ids=task_ids, reason=str(e))
                return

        try:
            for item in self.handle_filing_status(search_nos=search_nos, task_ids=task_ids):
                yield item
            for item in self.handle_release_status(search_nos=search_nos, task_ids=task_ids):
                yield item
        except (TimeoutError, NetworkError, PageError) as e:
            yield Restart(search_nos=search_nos, task_ids=task_ids, reason=str(e))
            return

        yield NextRoundRoutingRule.build_request_option(search_nos=search_nos, task_ids=task_ids)

    @staticmethod
    def _extract_hidden_info(response: scrapy.Selector) -> Dict:
        tables = response.css("table table")

        hidden_form_query = "form[name=frmCntrMove]"
        rule = CssQueryExistMatchRule(css_query=hidden_form_query)
        table_selector = find_selector_from(selectors=tables, rule=rule)
        if table_selector is None:
            raise CarrierResponseFormatError(reason="Can not found Basic Information table!!!")

        return {
            "mbl_no": table_selector.css("input[name=bl_no]::attr(value)").get(),
            "pol_code": table_selector.css("input[name=pol]::attr(value)").get(),
            "pod_code": table_selector.css("input[name=pod]::attr(value)").get(),
            "onboard_date": table_selector.css("input[name=onboard_date]::attr(value)").get(),
            "podctry": table_selector.css("input[name=podctry]::attr(value)").get(),
        }

    @staticmethod
    def _extract_basic_info(response: scrapy.Selector) -> Dict:
        tables = response.css("table table")

        rule = CssQueryTextStartswithMatchRule(css_query="td.f13tabb2::text", startswith="Basic Information")
        table_selector = find_selector_from(selectors=tables, rule=rule)
        if table_selector is None:
            raise CarrierResponseFormatError(reason="Can not found Basic Information table!!!")

        left_table_locator = LeftBasicInfoTableLocator()
        left_table_locator.parse(table=table_selector)
        left_table = TableExtractor(table_locator=left_table_locator)

        right_table_locator = RightBasicInfoTableLocator()
        right_table_locator.parse(table=table_selector)
        right_table = TableExtractor(table_locator=right_table_locator)

        return {
            "por_name": left_table.extract_cell(0, "Place of Receipt") or None,
            "pol_name": left_table.extract_cell(0, "Port of Loading") or None,
            "pod_name": left_table.extract_cell(0, "Port of Discharge") or None,
            "dest_name": left_table.extract_cell(0, "OCP Final Destination") or None,
            "place_of_deliv_name": left_table.extract_cell(0, "Place of Delivery") or None,
            "etd": right_table.extract_cell(0, "Estimated On Board Date") or None,
            "cargo_cutoff_date": right_table.extract_cell(0, "Cut Off Date") or None,
        }

    def _extract_vessel_info(self, response: scrapy.Selector, pod: str) -> Dict:
        tables = response.css("table table")

        rule = CssQueryTextStartswithMatchRule(css_query="td.f13tabb2::text", startswith="Plan Moves")
        table_selector = find_selector_from(selectors=tables, rule=rule)
        if table_selector is None:
            return {
                "eta": None,
                "vessel": None,
                "voyage": None,
            }

        table_locator = NameOnTopHeaderTableLocator()
        table_locator.parse(table=table_selector)
        table = TableExtractor(table_locator=table_locator)

        for left in table_locator.iter_left_header():
            if table.extract_cell("Location", left) == pod:
                vessel_voyage = table.extract_cell("Estimated Arrival Vessel/Voyage", left)
                vessel, voyage = self._get_vessel_voyage(vessel_voyage=vessel_voyage)
                return {
                    "eta": table.extract_cell("Estimated Arrival Date", left),
                    "vessel": vessel,
                    "voyage": voyage,
                }

        return {
            "eta": None,
            "vessel": None,
            "voyage": None,
        }

    @staticmethod
    def _get_vessel_voyage(vessel_voyage: str):
        if vessel_voyage == "To be Advised":
            return "", ""

        vessel, voyage = vessel_voyage.rsplit(sep=" ", maxsplit=1)
        return vessel, voyage

    @staticmethod
    def _extract_container_info(response: scrapy.Selector) -> List:
        tables = response.css("table table")

        rule = CssQueryTextStartswithMatchRule(
            css_query="td.f13tabb2::text",
            startswith="Container(s) information on B/L and Current Status",
        )
        table_selector = find_selector_from(selectors=tables, rule=rule)
        if table_selector is None:
            return []

        table_locator = NameOnTopHeaderTableLocator()
        table_locator.parse(table=table_selector)
        table = TableExtractor(table_locator=table_locator)

        return_list = []

        for left in table_locator.iter_left_header():
            return_list.append(
                {
                    "container_no": table.extract_cell("Container No.", left, FirstTextTdExtractor("a::text")),
                    "date": table.extract_cell("Date", left),
                }
            )

        return return_list

    @staticmethod
    def _check_filing_status(response: scrapy.Selector):
        tables = response.css("table")

        rule = CssQueryTextStartswithMatchRule(css_query="td a::text", startswith="Customs Information")
        return bool(find_selector_from(selectors=tables, rule=rule))

    @staticmethod
    def _get_first_container_no(container_list: List):
        return container_list[0]["container_no"]

    def handle_filing_status(self, search_nos: List, task_ids: List):
        httptext = asyncio.get_event_loop().run_until_complete(self.content_getter.custom_info_page())
        if httptext:
            response = self.get_response_selector(
                url=EGLV_INFO_URL, httptext=httptext, meta={"mbl_no": search_nos[0], "task_id": task_ids[0]}
            )
            rule = FilingStatusRoutingRule(task_id=task_ids[0])

            for item in rule.handle(response):
                yield item

    def handle_release_status(self, search_nos: List, task_ids: List):
        httptext = asyncio.get_event_loop().run_until_complete(self.content_getter.release_status_page())
        if httptext:
            response = self.get_response_selector(url=EGLV_INFO_URL, httptext=httptext, meta={"task_id": task_ids[0]})
            rule = ReleaseStatusRoutingRule(task_id=task_ids[0])

            for item in rule.handle(response):
                yield item


class LeftBasicInfoTableLocator(BaseTable):
    """
    +-----------------------------------+ <tbody>
    | Basic Information ...             | <tr>
    +---------+---------+-----+---------+
    | Title 1 | Data 1  |     |         | <tr>
    +---------+---------+-----+---------+
    | Title 2 | Data 2  |     |         | <tr>
    +---------+---------+-----+---------+
    | Title 3 | Data 3  |     |         | <tr>
    +---------+---------+-----+---------+
    | ...     |         |     |         | <tr>
    +---------+---------+-----+---------+
    | Title N | Data N  |     |         | <tr>
    +---------+---------+-----+---------+ </tbody>
    """

    TR_CONTENT_BEGIN_INDEX = 1
    TD_TITLE_INDEX = 0
    TD_DATA_INDEX = 1

    def parse(self, table: scrapy.Selector):
        content_tr_list = table.css("tr")[self.TR_CONTENT_BEGIN_INDEX :]

        for content_tr in content_tr_list:
            title_td = content_tr.css("td")[self.TD_TITLE_INDEX]
            data_td = content_tr.css("td")[self.TD_DATA_INDEX]

            title_text = title_td.css("::text").get().strip()
            self._left_header_set.add(title_text)
            td_dict = self._td_map.setdefault(0, {})
            td_dict[title_text] = data_td


class RightBasicInfoTableLocator(BaseTable):
    """
    +-----------------------------------+ <tbody>
    | Basic Information ...             | <tr>
    +-----+---------+---------+---------+
    |     |         | Title 1 | Data 1  | <tr>
    +-----+---------+---------+---------+
    |     |         | Title 2 | Data 2  | <tr>
    +-----+---------+---------+---------+
    |     |         | Title 3 | Data 3  | <tr>
    +-----+---------+---------+---------+
    |     |         | ...     | ...     | <tr>
    +-----+---------+---------+---------+
    |     |         | Title N | Data N  | <tr>
    +-----+---------+---------+---------+ </tbody>
    """

    TR_CONTENT_BEGIN_INDEX = 1
    TD_TITLE_INDEX = 2
    TD_DATA_INDEX = 3

    def parse(self, table: scrapy.Selector):
        content_tr_list = table.css("tr")[self.TR_CONTENT_BEGIN_INDEX :]

        for tr in content_tr_list:
            title_td = tr.css("td")[self.TD_TITLE_INDEX]
            data_td = tr.css("td")[self.TD_DATA_INDEX]

            title_text = title_td.css("::text").get().strip()
            self._left_header_set.add(title_text)
            td_dict = self._td_map.setdefault(0, {})
            td_dict[title_text] = data_td


# -------------------------------------------------------------------------------


class FilingStatusRoutingRule(BaseRoutingRule):
    name = "FILING_STATUS"

    def __init__(self, task_id: str):
        self.task_id = task_id

    @classmethod
    def build_request_option(cls, search_no: str, task_id: str, first_container_no: str, pod: str) -> RequestOption:
        form_data = {
            "TYPE": "GetDispInfo",
            "Item": "AMSACK",
            "BL": search_no,
            "firstCtnNo": first_container_no,
            "pod": pod,
        }

        return RequestOption(
            method=RequestOption.METHOD_POST_FORM,
            rule_name=cls.name,
            url=EGLV_INFO_URL,
            form_data=form_data,
            meta={
                "task_id": task_id,
            },
        )

    def get_save_name(self, response) -> str:
        return f"{self.name}.html"

    def handle(self, response):
        status = self._extract_filing_status(response=response)
        # task_id = response.meta["task_id"]

        yield MblItem(
            task_id=self.task_id,
            us_filing_status=status["filing_status"],
            us_filing_date=status["filing_date"],
        )

    @staticmethod
    def _extract_filing_status(response: scrapy.Selector) -> Dict:
        table_selector = response.css("table")

        if table_selector is None:
            return {
                "filing_status": None,
                "filing_date": None,
            }

        table_locator = NameOnTopHeaderTableLocator()
        table_locator.parse(table=table_selector)
        table = TableExtractor(table_locator=table_locator)

        for left in table_locator.iter_left_header():
            if table.extract_cell("Customs", left) == "US":
                return {
                    "filing_status": table.extract_cell("Description", left, FirstTextTdExtractor("a::text")),
                    "filing_date": table.extract_cell("Date", left),
                }

        return {
            "filing_status": None,
            "filing_date": None,
        }


# -------------------------------------------------------------------------------


class ReleaseStatusRoutingRule(BaseRoutingRule):
    name = "RELEASE_STATUS"

    def __init__(self, task_id: str):
        self.task_id = task_id

    @classmethod
    def build_request_option(cls, search_nos: List, task_ids: List) -> RequestOption:
        form_data = {
            "TYPE": "GetDispInfo",
            "Item": "RlsStatus",
            "BL": search_nos[0],
        }

        return RequestOption(
            method=RequestOption.METHOD_POST_FORM,
            rule_name=cls.name,
            url=EGLV_INFO_URL,
            form_data=form_data,
            meta={
                "search_nos": search_nos,
                "task_ids": task_ids,
            },
        )

    def get_save_name(self, response) -> str:
        return f"{self.name}.html"

    def handle(self, response):
        # task_id = response.meta["task_ids"][0]
        release_status = self._extract_release_status(response=response)

        yield MblItem(
            task_id=self.task_id,
            carrier_status=release_status["carrier_status"],
            carrier_release_date=release_status["carrier_release_date"],
            us_customs_status=release_status["us_customs_status"],
            us_customs_date=release_status["us_customs_date"],
            customs_release_status=release_status["customs_release_status"],
            customs_release_date=release_status["customs_release_date"],
        )

    @staticmethod
    def _extract_release_status(response: scrapy.Selector) -> Dict:
        table_selector = response.css("table")

        if not table_selector:
            return {
                "carrier_status": None,
                "carrier_release_date": None,
                "us_customs_status": None,
                "us_customs_date": None,
                "customs_release_status": None,
                "customs_release_date": None,
            }

        first_message = table_selector.css("tr td::text").get()
        if first_message.strip() == "Data not found.":
            return {
                "carrier_status": None,
                "carrier_release_date": None,
                "us_customs_status": None,
                "us_customs_date": None,
                "customs_release_status": None,
                "customs_release_date": None,
            }

        carrier_status_table_locator = CarrierStatusTableLocator()
        carrier_status_table_locator.parse(table=table_selector)
        carrier_status_table = TableExtractor(table_locator=carrier_status_table_locator)

        us_customs_status_table_locator = USCustomStatusTableLocator()
        us_customs_status_table_locator.parse(table=table_selector)
        us_customs_status_table = TableExtractor(table_locator=us_customs_status_table_locator)

        custom_release_status_table_locator = CustomReleaseStatusTableLocator()
        custom_release_status_table_locator.parse(table=table_selector)
        custom_release_status_table = TableExtractor(table_locator=custom_release_status_table_locator)

        return {
            "carrier_status": carrier_status_table.extract_cell(top="Status") or None,
            "carrier_release_date": carrier_status_table.extract_cell(top="Carrier Date") or None,
            "us_customs_status": us_customs_status_table.extract_cell(top="I.T. NO.") or None,
            "us_customs_date": us_customs_status_table.extract_cell(top="Date") or None,
            "customs_release_status": custom_release_status_table.extract_cell(top="Status") or None,
            "customs_release_date": custom_release_status_table.extract_cell(top="Date") or None,
        }


class CarrierStatusTableLocator(BaseTable):
    """
    +---------------------------------------------------------------+ <tbody>
    | Release Status                                                | <tr>
    +---------+----------+---------+---------+-----------+----------+
    | Carrier | Title 1  | Title 2 | Title 3 |  Title 4  | Title 5  | <tr>
    |         +----------+---------+---------+-----------+----------+
    | Status  | Data 1   | Data 2  | Data 3  |  Data 4   | Data 5   | <tr>
    +---------+----------+---------+---------+-----------+----------+
    |         |          |                   |           |          | <tr>
    |         +----------+-------------------+-----------+----------+
    |         |          |                   |           |          | <tr>
    |         +----------+-------------------+-----------+----------+
    |         |          |                               |          | <tr>
    |         +----------+-------------------------------+----------+
    |         |          |                               |          | <tr>
    +---------+----------+-------------------------------+----------+ </tbody>
    """

    TR_TITLE_INDEX = 1
    TR_DATA_INDEX = 2

    def __init__(self):
        super().__init__()

        self._title_remap = {  # title_index: rename title
            3: "Carrier Date",
            5: "Way Bill Date",
        }

    def parse(self, table: scrapy.Selector):
        title_tr = table.css("tr")[self.TR_TITLE_INDEX]
        data_tr = table.css("tr")[self.TR_DATA_INDEX]

        title_text_list = title_tr.css("td::text").getall()
        data_td_list = data_tr.css("td")
        self._left_header_set.add(0)

        for data_index, data_td in enumerate(data_td_list):
            title_index = data_index + 1  # index shift by row span
            title_text = title_text_list[title_index].strip()

            new_title_text = self._title_remap.get(title_index, title_text)

            self._td_map.setdefault(new_title_text, [])
            self._td_map[new_title_text].append(data_td)


class USCustomStatusTableLocator(BaseTable):
    """
    +----------------------------------------------------------------+ <tbody>
    | Release Status                                                 | <tr>
    +---------+----------+---------+---------+------------+----------+
    |         |          |         |         |            |          | <tr>
    +         +----------+---------+---------+------------+----------+
    |         |          |         |         |            |          | <tr>
    +---------+----------+---------+---------+------------+----------+
    | Customs | Title 1  |     Title 2       |  Title 3   | Title 4  | <tr>
    |         +----------+-------------------+------------+----------+
    |         | Data 1   |     Data 2        |  Data 3    | Data 4   | <tr>
    |         +----------+-------------------+------------+----------+
    | Status  |          |                                |          | <tr>
    |         +----------+--------------------------------+----------+
    |         |          |                                |          | <tr>
    +---------+----------+--------------------------------+----------+ </tbody>
    """

    TR_TITLE_INDEX = 3
    TR_DATA_INDEX = 4

    def parse(self, table: scrapy.Selector):
        title_tr = table.css("tr")[self.TR_TITLE_INDEX]
        data_tr = table.css("tr")[self.TR_DATA_INDEX]

        title_text_list = title_tr.css("td::text").getall()
        data_td_list = data_tr.css("td")
        self._left_header_set.add(0)

        for data_index, data_td in enumerate(data_td_list):
            title_index = data_index + 1  # index shift by row span

            title_text = title_text_list[title_index].strip()

            self._td_map.setdefault(title_text, [])
            self._td_map[title_text].append(data_td)


class CustomReleaseStatusTableLocator(BaseTable):
    """
    +----------------------------------------------------------------+ <tbody>
    | Release Status                                                 | <tr>
    +---------+----------+---------+---------+------------+----------+
    |         |          |         |         |            |          | <tr>
    |         +----------+---------+---------+------------+----------+
    |         |          |         |         |            |          | <tr>
    +---------+----------+---------+---------+------------+----------+
    | Customs |          |                   |            |          | <tr>
    |         +----------+-------------------+------------+----------+
    |         |          |                   |            |          | <tr>
    |         +----------+-------------------+------------+----------+
    | Status  | Title 1  |             Title 2            | Title 3  | <tr>
    |         +----------+--------------------------------+----------+
    |         | Data 1   |             Data 2             | Data 3   | <tr>
    +---------+----------+--------------------------------+----------+ </tbody>
    """

    TR_TITLE_INDEX = 5
    TR_DATA_INDEX = 6

    def parse(self, table: scrapy.Selector):
        title_tr = table.css("tr")[self.TR_TITLE_INDEX]
        data_tr = table.css("tr")[self.TR_DATA_INDEX]

        title_text_list = title_tr.css("td::text").getall()
        data_td_list = data_tr.css("td")
        self._left_header_set.add(0)

        for data_index, data_td in enumerate(data_td_list):
            title_index = data_index

            title_text = title_text_list[title_index].strip()

            self._td_map.setdefault(title_text, [])
            self._td_map[title_text].append(data_td)


# -------------------------------------------------------------------------------


class ContainerStatusRoutingRule(BaseRoutingRule):
    name = "CONTAINER_STATUS"

    @classmethod
    def build_request_option(
        cls,
        search_no: str,
        task_id: str,
        container_no: str,
        onboard_date: str,
        pol: str,
        pod: str = "",
        podctry: str = "",
    ) -> RequestOption:
        form_data = {
            "bl_no": search_no,
            "cntr_no": container_no,
            "onboard_date": onboard_date,
            "pol": pol,
            "TYPE": "CntrMove",
        }

        if pod and podctry:
            form_data.update(
                {
                    "pod": pod,
                    "podctry": podctry,
                }
            )

        return RequestOption(
            method=RequestOption.METHOD_POST_FORM,
            rule_name=cls.name,
            url=EGLV_INFO_URL,
            form_data=form_data,
            meta={
                "container_no": container_no,
                "task_id": task_id,
            },
        )

    def get_save_name(self, response) -> str:
        container_no = response.meta["container_no"]
        return f"{self.name}_{container_no}.html"

    def handle(self, response):
        task_id = response.meta["task_id"]
        container_no = response.meta["container_no"]

        container_status_list = self._extract_container_status_list(response=response)
        for container_status in container_status_list:
            yield ContainerStatusItem(
                task_id=task_id,
                container_key=container_no,
                description=container_status["description"],
                local_date_time=container_status["timestamp"],
                location=LocationItem(name=container_status["location_name"]),
            )

    @staticmethod
    def _extract_container_status_list(response: scrapy.Selector) -> List[Dict]:
        container_status_list = []

        tables = response.css("table table")

        rule = CssQueryTextStartswithMatchRule(css_query="td::text", startswith="Container Moves")
        table_selector = find_selector_from(selectors=tables, rule=rule)
        if table_selector is None:
            return container_status_list

        table_locator = NameOnTopHeaderTableLocator()
        table_locator.parse(table=table_selector)
        table = TableExtractor(table_locator=table_locator)

        for left in table_locator.iter_left_header():
            container_status_list.append(
                {
                    "timestamp": table.extract_cell("Date", left),
                    "description": table.extract_cell("Container Moves", left),
                    "location_name": table.extract_cell("Location", left),
                }
            )

        return container_status_list


# -------------------------------------------------------------------------------


class BookingMainInfoRoutingRule(MainInfoRoutingRule):
    name = "BOOKING_MAIN_INFO"

    def __init__(self, content_getter):
        super().__init__(content_getter)

    @classmethod
    def build_request_option(cls, search_nos: List, verification_code: str, task_ids: List) -> RequestOption:
        form_data = {
            "BL": "",
            "CNTR": "",
            "bkno": search_nos[0],
            "TYPE": "BK",
            "NO": ["", "", "", "", "", ""],
            "SEL": "s_bk",
            "captcha_input": verification_code,
            "hd_captcha_input": "",
        }

        return RequestOption(
            method=RequestOption.METHOD_POST_FORM,
            rule_name=cls.name,
            url=EGLV_INFO_URL,
            form_data=form_data,
            meta={
                "search_nos": search_nos,
                "task_ids": task_ids,
            },
        )

    def get_save_name(self, response) -> str:
        return f"{self.name}.html"

    def handle(self, response):
        # Apply NextRoundRoutingRule inside of it
        for item in self._handle_main_info_page(response=response):
            yield item

    @staticmethod
    def _check_captcha(response) -> bool:
        # wrong captcha -> back to search page
        message_under_search_table = " ".join(
            response.css('table table[cellpadding="1"] tr td.f12rown1::text').getall()
        )
        if isinstance(message_under_search_table, str):
            message_under_search_table = message_under_search_table.strip()
        back_to_search_page_message = "Shipments tracing by Booking NO. is available for specific countries/areas only."

        if message_under_search_table == back_to_search_page_message:
            return False
        else:
            return True

    def _handle_main_info_page(self, response):
        task_ids = response.meta["task_ids"]
        search_nos = response.meta["search_nos"]

        booking_no_and_vessel_voyage = self._extract_booking_no_and_vessel_voyage(response=response)
        basic_info = self._extract_basic_info(response=response)
        filing_info = self._extract_filing_info(response=response)

        yield MblItem(
            task_id=task_ids[0],
            booking_no=booking_no_and_vessel_voyage["booking_no"],
            por=LocationItem(name=basic_info["por_name"]),
            pol=LocationItem(name=basic_info["pol_name"]),
            pod=LocationItem(name=basic_info["pod_name"]),
            place_of_deliv=LocationItem(name=basic_info["place_of_deliv_name"]),
            etd=basic_info["etd"],
            eta=basic_info["eta"],
            cargo_cutoff_date=basic_info["cargo_cutoff_date"],
            est_onboard_date=basic_info["onboard_date"],
            us_filing_status=filing_info["filing_status"],
            us_filing_date=filing_info["filing_date"],
            vessel=booking_no_and_vessel_voyage["vessel"],
            voyage=booking_no_and_vessel_voyage["voyage"],
        )

        # hidden_form_info = self._extract_hidden_form_info(response=response)
        container_infos = self._extract_container_infos(response=response)
        for container_info in container_infos:
            yield ContainerItem(
                task_id=task_ids[0],
                container_key=container_info.get("container_no", ""),
                container_no=container_info.get("container_no", ""),
                full_pickup_date=container_info.get("full_pickup_date", ""),
            )

            try:
                for item in self.handle_container_status(
                    container_no=container_info["container_no"], search_nos=search_nos, task_ids=task_ids
                ):
                    yield item
            except (TimeoutError, NetworkError, PageError) as e:
                yield Restart(search_nos=search_nos, task_ids=task_ids, reason=str(e))
                return

        yield NextRoundRoutingRule.build_request_option(search_nos=search_nos, task_ids=task_ids)

    def _extract_booking_no_and_vessel_voyage(self, response: scrapy.Selector) -> Dict:
        tables = response.css("table table")
        rule = CssQueryExistMatchRule(css_query="td.f12wrdb2")
        table = find_selector_from(selectors=tables, rule=rule)

        data_tds = table.css("td.f12wrdb2")[1:]  # first td is icon
        booking_no = data_tds[0]
        vessel_voyage_td = data_tds[1]

        booking_no = booking_no.css("::text").get().strip()
        raw_vessel_voyage = vessel_voyage_td.css("::text").get().strip()
        vessel, voyage = self._re_parse_vessel_voyage(vessel_voyage=raw_vessel_voyage)

        return {
            "booking_no": booking_no,
            "vessel": vessel,
            "voyage": voyage,
        }

    @staticmethod
    def _re_parse_vessel_voyage(vessel_voyage: str):
        """
        ex:
        EVER LINKING 0950-041E\n\n\t\t\t\t\xa0(長連輪)
        """
        pattern = re.compile(r"(?P<vessel>[\D]+)\s(?P<voyage>[\w-]+)[^(]*(\(.+\))?")
        match = pattern.match(vessel_voyage)
        if not match:
            raise CarrierResponseFormatError(reason=f"Unexpected vessel_voyage `{vessel_voyage}`")
        return match.group("vessel"), match.group("voyage")

    @staticmethod
    def _extract_basic_info(response: scrapy.Selector) -> Dict:
        tables = response.css("table table")
        rule = FirstCellTextMatch(text="Basic Information")
        table = find_selector_from(selectors=tables, rule=rule)

        table_locator = BookingBasicUpperTopLeftTableLocator()
        table_locator.parse(table=table)
        table_extractor = TableExtractor(table_locator=table_locator)

        pol_cutoff_date = table_extractor.extract_cell(top="Cut Off Date", left="Port of Loading")
        por_cutoff_date = table_extractor.extract_cell(top="Cut Off Date", left="Place of Receipt")
        if pol_cutoff_date:
            cutoff_date = pol_cutoff_date
        else:
            cutoff_date = por_cutoff_date

        return {
            "por_name": table_extractor.extract_cell(top="Location", left="Place of Receipt"),
            "pol_name": table_extractor.extract_cell(top="Location", left="Port of Loading"),
            "pod_name": table_extractor.extract_cell(top="Location", left="Port of Discharge"),
            "place_of_deliv_name": table_extractor.extract_cell(top="Location", left="Place of Delivery"),
            "cargo_cutoff_date": cutoff_date,
            "etd": table_extractor.extract_cell(top="Estimated Departure Date", left="Port of Loading"),
            "eta": table_extractor.extract_cell(top="Estimated Arrival Date", left="Port of Discharge"),
            "onboard_date": table_extractor.extract_cell(top="Estimated On Board Date", left="Port of Loading"),
        }

    @staticmethod
    def _extract_filing_info(response: scrapy.Selector) -> Dict:
        tables = response.css("table")
        rule = CssQueryTextStartswithMatchRule(css_query="td.f13tabb2::text", startswith="Advance Filing Status")
        table = find_selector_from(selectors=tables, rule=rule)
        if not table:
            return {
                "filing_status": None,
                "filing_date": None,
            }

        table_locator = NameOnTopHeaderTableLocator()
        table_locator.parse(table=table)
        table_extractor = TableExtractor(table_locator=table_locator)

        return {
            "filing_status": table_extractor.extract_cell(top="Description", left=0),
            "filing_date": table_extractor.extract_cell(top="Date", left=0),
        }

    @staticmethod
    def _extract_hidden_form_info(response: scrapy.Selector) -> Dict:
        tables = response.css("br + table")
        rule = CssQueryTextStartswithMatchRule(
            css_query="td.f12rowb4::text", startswith="Container Activity Information"
        )
        table = find_selector_from(selectors=tables, rule=rule)

        return {
            "bl_no": table.css("input[name='bl_no']::attr(value)").get(),
            "onboard_date": table.css("input[name='onboard_date']::attr(value)").get(),
            "pol": table.css("input[name='pol']::attr(value)").get(),
            "TYPE": table.css("input[name='TYPE']::attr(value)").get(),
        }

    @staticmethod
    def _extract_container_infos(response: scrapy.Selector) -> List[Dict]:
        container_infos = []

        tables = response.css("br + table")
        rule = CssQueryTextStartswithMatchRule(
            css_query="td.f12rowb4::text", startswith="Container Activity Information"
        )
        table = find_selector_from(selectors=tables, rule=rule)
        table_locator = NameOnTopHeaderTableLocator()
        table_locator.parse(table=table)
        table_extractor = TableExtractor(table_locator=table_locator)

        date_pattern = re.compile(r"\w+-\d+-\d+\s\d+:\d+")  # "MAY-10-2021 16:31"

        for left in table_locator.iter_left_header():
            # there are no Empty Out info in some of the bookings
            # full_date_cell = table_extractor.extract_cell(top="Empty Out", left=left)
            empty_date_cell = table_extractor.extract_cell(top="Full return to", left=left)

            full_pickup_date = None
            # if full_date_cell:
            #     full_pickup_date_search = date_pattern.search(full_date_cell)
            #     full_pickup_date = full_pickup_date_search.group(0) if full_pickup_date_search else ""

            empty_pickup_date_search = date_pattern.search(empty_date_cell)
            empty_pickup_date = empty_pickup_date_search.group(0) if empty_pickup_date_search else ""

            container_infos.append(
                {
                    "container_no": table_extractor.extract_cell(
                        top="Container No.", left=left, extractor=FirstTextTdExtractor(css_query="a::text")
                    ),
                    "full_pickup_date": full_pickup_date,
                    "empty_pickup_date": empty_pickup_date,
                }
            )

        return container_infos


class FirstCellTextMatch(BaseMatchRule):
    def __init__(self, text):
        self._text = text

    def check(self, selector: scrapy.Selector) -> bool:
        first_cell = selector.css("tr")[0].css("td")[0]
        raw_first_cell_text = first_cell.css("::text").get()

        first_cell_text = raw_first_cell_text.strip() if isinstance(raw_first_cell_text, str) else raw_first_cell_text
        return self._text == first_cell_text


class BookingBasicUpperTopLeftTableLocator(BaseTable):
    TR_TOP_TITLE_INDEX = 1
    TD_TOP_TITLE_LOCATION_INDEX = 0
    TR_DATA_START_INDEX = 2
    TD_LEFT_TITLE_INDEX = 0
    TD_DATA_START_INDEX = 1
    LEFT_TITLE_LIST = ["Place of Receipt", "Port of Loading", "Port of Discharge", "Place of Delivery"]

    def parse(self, table: scrapy.Selector):
        trs = table.css("tr")
        title_tr = trs[self.TR_TOP_TITLE_INDEX]
        data_trs = trs[self.TR_DATA_START_INDEX :]

        top_title_list = []
        for title_i, title_td in enumerate(title_tr.css("td")):
            if title_i == self.TD_TOP_TITLE_LOCATION_INDEX:
                title = "Location"
            else:
                raw_title_texts = title_td.css("::text").getall()
                title_texts = [title_text.strip() for title_text in raw_title_texts]
                title = " ".join(title_texts)

            self._td_map.setdefault(title, {})
            top_title_list.append(title)

        for data_tr in data_trs:
            data_tds = data_tr.css("td")

            left_title = data_tds[self.TD_LEFT_TITLE_INDEX].css("::text").get().strip()
            if left_title not in self.LEFT_TITLE_LIST:
                continue
            self.add_left_header_set(left_title)

            for top_title in top_title_list:
                self._td_map[top_title][left_title] = scrapy.Selector(text="<td></td>")

            now_td_i = 0
            for data_td in data_tds[self.TD_DATA_START_INDEX :]:
                raw_colspan = data_td.css("::attr(colspan)").get()
                colspan = int(raw_colspan) if raw_colspan else 1

                top_title_i = now_td_i
                top_title = top_title_list[top_title_i]
                self._td_map[top_title][left_title] = data_td

                # next iter
                next_td_i = now_td_i + colspan
                now_td_i = next_td_i


# -------------------------------------------------------------------------------


class NameOnTopHeaderTableLocator(BaseTable):
    """
    +-----------------------------------+ <tbody>
    | Table Name                        | <tr>
    +---------+---------+-----+---------+
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

    TR_TITLE_INDEX = 1
    TR_DATA_BEGIN_INDEX = 2

    def parse(self, table: scrapy.Selector):
        title_tr = table.css("tr")[self.TR_TITLE_INDEX]

        data_tr_list = table.xpath("./tr | ./tbody/tr")[self.TR_DATA_BEGIN_INDEX :]
        self._left_header_set = set(range(len(data_tr_list)))

        title_text_list = title_tr.css("td::text").getall()

        for title_index, title_text in enumerate(title_text_list):
            data_index = title_index

            title_text = title_text.strip()
            self._td_map[title_text] = []

            for data_tr in data_tr_list:
                data_td = data_tr.css("td")[data_index]

                self._td_map[title_text].append(data_td)


class NextRoundRoutingRule(BaseRoutingRule):
    name = "ROUTING"

    @classmethod
    def build_request_option(cls, search_nos: List, task_ids: List) -> RequestOption:
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url="https://eval.edi.hardcoretech.co/c/livez",
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

        yield CargoTrackingRoutingRule.build_request_option(search_nos=search_nos, task_ids=task_ids)


class CaptchaAnalyzer:
    SERVICE_URL = "https://nymnwfny58.execute-api.us-west-2.amazonaws.com/dev/captcha-eglv"
    headers = {
        "x-api-key": "jzeitRn28t5UMxRA31Co46PfseW9hTK43DLrBtb6",
    }

    def analyze_captcha(self, captcha_base64: bytes) -> str:
        req = requests.post(url=self.SERVICE_URL, data=captcha_base64, headers=self.headers)
        return req.content


class EglvContentGetter(PyppeteerContentGetter):
    MAX_CAPTCHA_RETRY = 3

    def __init__(self, proxy_manager: ProxyManager = None, is_headless: bool = False):
        super().__init__(proxy_manager, is_headless=is_headless)

    async def search_and_return(self, search_no: str, search_type: str):
        btn_value = "s_bl" if search_type == SHIPMENT_TYPE_MBL else "s_bk"
        self.page.on("dialog", lambda dialog: asyncio.ensure_future(self.close_dialog(dialog)))

        await self.page.goto(EGLV_INFO_URL)
        await self.page.waitForSelector(f"input[value={btn_value}]", {"timeout": 10000})
        await self.page.waitForSelector("input#NO")

        await self.page.click(f"input[value={btn_value}]")
        await self.page.type("input#NO", search_no)
        await asyncio.sleep(2)
        await self.page.click("#quick input[type=button]")

        max_check_times = 2
        while (max_check_times != 0) and (await self._check_data_exist()):
            max_check_times -= 1

        is_exist = await self._check_data_exist()
        content = await self.page.content()
        await self.scroll_down()

        return content, is_exist

    async def _check_data_exist(self):
        try:
            await self.page.waitForSelector('table[cellpadding="2"]', {"timeout": 10000})
            return True
        except TimeoutError:
            return False

    async def handle_captcha(self):
        captcha_analyzer = CaptchaAnalyzer()
        element = await self.page.querySelector("div#captcha_div > img#captchaImg")
        get_base64_func = """(img) => {
                        var canvas = document.createElement("canvas");
                        canvas.width = 150;
                        canvas.height = 40;
                        var ctx = canvas.getContext("2d");
                        ctx.drawImage(img, 0, 0);
                        var dataURL = canvas.toDataURL("image/png");
                        return dataURL.replace(/^data:image/(png|jpg);base64,/, "");
                    }
                    """
        captcha_base64 = await self.page.evaluate(get_base64_func, element)
        verification_code = captcha_analyzer.analyze_captcha(captcha_base64=captcha_base64).decode("utf-8")
        await self.page.type("div#captcha_div > input#captcha_input", verification_code)
        await asyncio.sleep(2)

    @staticmethod
    async def close_dialog(dialog: Dialog):
        await asyncio.sleep(2)
        await dialog.dismiss()

    async def custom_info_page(self) -> str:
        try:
            await self.page.click("a[href=\"JavaScript:toggle('CustomsInfo');\"]")
            await asyncio.sleep(1)
            while not await self.page.xpath("//div[@id='CustomsInfo' and contains(@style, 'display: block')]"):
                await asyncio.sleep(1)

            await self.page.click("a[href=\"JavaScript:getDispInfo('AMTitle','AMInfo');\"]")
            await self.page.waitForSelector("div#AMInfo table")
            await asyncio.sleep(10)
            div_ele = await self.page.querySelector("div#AMInfo")
            return await self.page.evaluate("(element) => element.outerHTML", div_ele)
        except PageError:
            return ""

    async def release_status_page(self) -> str:
        try:
            await self.page.click("a[href=\"JavaScript:getDispInfo('RlsStatusTitle','RlsStatusInfo');\"]")
            await self.page.waitForSelector("div#RlsStatusInfo table")
            await asyncio.sleep(2)
            await self.scroll_down()
            div_ele = await self.page.querySelector("div#RlsStatusInfo")
            return await self.page.evaluate("(element) => element.outerHTML", div_ele)
        except PageError:
            return ""

    async def container_page(self, container_no) -> str:
        try:
            await self.scroll_down()
            await self.page.click(f"a[href^=\"javascript:frmCntrMoveDetail('{container_no}')\"]")
            await asyncio.sleep(10)
            container_page = (await self.browser.pages())[-1]
            await container_page.waitForSelector("table table")
            await asyncio.sleep(5)
            content = await container_page.content()
            await container_page.close()
            return content
        except PageError:
            return ""
