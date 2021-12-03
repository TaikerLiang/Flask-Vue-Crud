import re
from typing import Dict, List
from urllib.parse import urlencode

import scrapy

from crawler.core_carrier.base_spiders import BaseCarrierSpider
from crawler.core_carrier.exceptions import SuspiciousOperationError
from crawler.core_carrier.base import CARRIER_RESULT_STATUS_ERROR
from crawler.core_carrier.items import (
    BaseCarrierItem,
    MblItem,
    ContainerItem,
    ContainerStatusItem,
    LocationItem,
    VesselItem,
    ExportErrorData,
    DebugItem,
)
from crawler.core_carrier.request_helpers import RequestOption
from crawler.core_carrier.rules import RuleManager, BaseRoutingRule
from crawler.core.table import BaseTable, TableExtractor

URL = "https://www.sethshipping.com/track_shipment_ajax"


class SharedSpider(BaseCarrierSpider):
    name = None

    def __init__(self, *args, **kwargs):
        super(SharedSpider, self).__init__(*args, **kwargs)

        rules = [
            MainInfoRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)

    def start(self):
        request_option = MainInfoRoutingRule.build_request_option(mbl_no=self.mbl_no)
        yield self._build_request_by(option=request_option)

    def parse(self, response):
        yield DebugItem(info={"meta": dict(response.meta)})

        routing_rule = self._rule_manager.get_rule_by_response(response=response)

        save_name = routing_rule.get_save_name(response=response)
        self._saver.save(to=save_name, text=response.text)

        for result in routing_rule.handle(response=response):
            if isinstance(result, BaseCarrierItem):
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
            )
        elif option.method == RequestOption.METHOD_POST_BODY:
            return scrapy.Request(
                method="POST",
                url=option.url,
                headers=option.headers,
                body=option.body,
                meta=meta,
                dont_filter=True,
            )
        else:
            raise SuspiciousOperationError(msg=f"Unexpected request method: `{option.method}`")


class CarrierSsphSpider(SharedSpider):
    name = "carrier_ssph"


class CarrierGosuSpider(SharedSpider):
    name = "carrier_gosu"


class MainInfoRoutingRule(BaseRoutingRule):
    name = "MAIN_INFO"

    @classmethod
    def build_request_option(cls, mbl_no) -> RequestOption:
        form_data = {"containerid": mbl_no}
        body = urlencode(query=form_data)
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_POST_BODY,
            url=URL,
            headers={
                "Connection": "keep-alive",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Referer": "https://www.sethshipping.com/tracking_shipment?id=SSPHAMD1234567",
                "Accept-Language": "en-US,en;q=0.9",
            },
            body=body,
            meta={
                "mbl_no": mbl_no,
            },
        )

    def get_save_name(self, response) -> str:
        return f"{self.name}.html"

    def handle(self, response):
        mbl_no = response.meta["mbl_no"]
        if self._is_mbl_no_invalid(response=response):
            yield ExportErrorData(mbl_no=mbl_no, status=CARRIER_RESULT_STATUS_ERROR, detail="Data was not found")
            return

        mbl_no = self._extract_mbl_no(response=response)
        main_info = self._extract_main_info(response=response)

        yield MblItem(
            mbl_no=mbl_no or None,
            pol=LocationItem(name=main_info["pol_name"]),
            pod=LocationItem(name=main_info["pod_name"]),
            por="",
            final_dest=LocationItem(name=main_info["final_dest_name"]),
            eta=main_info["eta"],
        )

        vessel_info_list = self._extract_vessel_info_list(response=response)

        for vessel_info in vessel_info_list:
            yield VesselItem(
                vessel_key=vessel_info["vessel"],
                vessel=vessel_info["vessel"],
                voyage=vessel_info["voyage"],
                eta=vessel_info["eta"],
                etd=vessel_info["etd"],
                pol=LocationItem(name=vessel_info["pol_name"]),
                pod=LocationItem(name=vessel_info["pod_name"]),
            )

        container_info_list = self._extract_container_info(response=response)

        for idx, container_info in enumerate(container_info_list):
            container_no = container_info["container_no"]
            container_key = container_info["container_no"]
            yield ContainerItem(
                container_key=container_key,
                container_no=container_no,
            )

            container_status_list = self._extract_container_status(response=response, idx=idx)

            for status in container_status_list:
                yield ContainerStatusItem(
                    container_key=container_key,
                    description=status["description"],
                    location=LocationItem(name=status["location_name"]),
                    local_date_time=status["local_date_time"],
                )

    @staticmethod
    def _is_mbl_no_invalid(response):
        data_found_selector = response.css("table")
        return not bool(data_found_selector)

    @staticmethod
    def _extract_mbl_no(response):
        table = response.css("table.table")
        mbl_no = table.xpath("//thead/th/h3/text()").get()
        return mbl_no.strip()

    @staticmethod
    def _extract_main_info(response) -> Dict:
        left_table = response.css("table")[1]
        right_table = response.css("table")[2]
        table_locator = MainInfoTableLocator()
        table_locator.parse(table=left_table)
        table_locator.parse(table=right_table)
        table_extractor = TableExtractor(table_locator=table_locator)

        return {
            "por_name": table_extractor.extract_cell(left="Final Destination:") or None,
            "pol_name": table_extractor.extract_cell(left="Port of Loading (POL)") or None,
            "pod_name": table_extractor.extract_cell(left="Port of Discharge (POD)") or None,
            "final_dest_name": table_extractor.extract_cell(left="Final Destination:") or None,
            "eta": table_extractor.extract_cell(left="Estimated Time of Arrival") or None,
        }

    @staticmethod
    def _extract_vessel_info_list(response) -> List:
        return_list = []
        tables = response.css("div.table-responsive.p-1>table")
        for table in tables:
            table_locator = VesselTableLocator()
            table_locator.parse(table=table)
            table_extractor = TableExtractor(table_locator=table_locator)
            pol = pod = etd = eta = None
            if table_extractor.has_header(top="Port of Loading"):
                pol = table_extractor.extract_cell(top="Port of Loading")
            if table_extractor.has_header(top="Port of Discharge"):
                pod = table_extractor.extract_cell(top="Port of Discharge")
            if table_extractor.has_header(top="ETD"):
                etd = table_extractor.extract_cell(top="ETD")
            if table_extractor.has_header(top="ETA"):
                eta = table_extractor.extract_cell(top="ETA")
            if table_extractor.has_header(top="Vessel / Voyage"):
                vessel_voyage = table_extractor.extract_cell(top="Vessel / Voyage")
            else:
                vessel_voyage = ""
            vessel_voyage_pattern = re.compile(r"^(?P<vessel>.+)/(?P<voyage>.+)$")
            vessel_voyage_match = vessel_voyage_pattern.match(vessel_voyage)
            if vessel_voyage_match:
                vessel = vessel_voyage_match.group("vessel")
                voyage = vessel_voyage_match.group("voyage")
            else:
                vessel = None
                voyage = None

            if pol or pod:
                return_list.append(
                    {
                        "etd": etd,
                        "eta": eta,
                        "vessel": vessel,
                        "voyage": voyage,
                        "pol_name": pol,
                        "pod_name": pod,
                    }
                )

        return return_list

    @staticmethod
    def _extract_container_info(response) -> List:

        table = response.css("div.table-responsive:not(.p-1)>table")
        table_locator = ContainerTableLocator()
        table_locator.parse(table=table)
        table_extractor = TableExtractor(table_locator=table_locator)

        return_list = []
        for left in table_locator.iter_left_header():
            return_list.append(
                {
                    "container_no": table_extractor.extract_cell(top="Container", left=left).split()[0],
                    "eta": table_extractor.extract_cell(top="Date", left=left),
                }
            )

        return return_list

    @staticmethod
    def _extract_container_status(response, idx) -> List:
        table = response.css(f"div#collapse{idx+1} table")
        table_locator = ContainerStatusTableLocator()
        table_locator.parse(table=table)
        table_extractor = TableExtractor(table_locator=table_locator)

        return_list = []
        for left in table_locator.iter_left_header():
            return_list.append(
                {
                    "description": table_extractor.extract_cell(top="Last Activity", left=left),
                    "location_name": table_extractor.extract_cell(top="Location", left=left),
                    "local_date_time": table_extractor.extract_cell(top="Date", left=left),
                }
            )

        return return_list

    @staticmethod
    def _get_local_date_time_and_location(local_date_time_text: str):
        pattern = re.compile(r"^(?P<local_date_time>\d{2}-\w{3}-\d{4}), (?P<location>.+)$")

        m = pattern.match(local_date_time_text)
        if m:
            local_date_time = m.group("local_date_time")
            location = m.group("location")
        else:
            local_date_time = None
            location = local_date_time_text

        return local_date_time, location


class MainInfoTableLocator(BaseTable):
    def parse(self, table: scrapy.Selector):
        td_dict = self._td_map.setdefault(0, {})
        for tr in table.css("tr"):
            label = tr.css("td ::text")[0].get().strip()
            self._left_header_set.add(label)
            content = tr.css("td")[1]
            td_dict[label] = content


class VesselTableLocator(BaseTable):
    def parse(self, table: scrapy.Selector):
        self._left_header_set.add(0)
        for tr in table.css("tr"):
            for td in tr.css("td"):
                if td.css("p"):
                    label = td.css("p ::text")[0].get().strip()
                    content = td.css("p")[1]
                    self._td_map[label] = [content]


class ContainerTableLocator(BaseTable):
    def parse(self, table: scrapy.Selector):
        top_header_list = []

        head = table.css("thead")[0]
        for th in head.css("th"):
            raw_top_header = th.css("::text").get()
            top_header = raw_top_header.strip() if isinstance(raw_top_header, str) else ""
            top_header_list.append(top_header)
            self._td_map[top_header] = []

        data_tr_list = table.css("tbody tr.accordion-toggle.collapsed")
        for index, tr in enumerate(data_tr_list):
            self._left_header_set.add(index)
            for top, td in zip(top_header_list, tr.css("td")):
                self._td_map[top].append(td)


class ContainerStatusTableLocator(BaseTable):
    def parse(self, table: scrapy.Selector):
        top_header_list = []

        head = table.css("thead")[0]
        for th in head.css("th"):
            raw_top_header = th.css("::text").get()
            top_header = raw_top_header.strip() if isinstance(raw_top_header, str) else ""
            top_header_list.append(top_header)
            self._td_map[top_header] = []

        data_tr_list = table.css("tbody tr")
        for index, tr in enumerate(data_tr_list):
            self._left_header_set.add(index)
            for top, td in zip(top_header_list, tr.css("td")):
                self._td_map[top].append(td)
