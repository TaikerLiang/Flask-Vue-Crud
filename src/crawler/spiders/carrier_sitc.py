import re
import string
import random
from typing import Dict, List

import scrapy
from anticaptchaofficial.imagecaptcha import *

from crawler.core_carrier.base_spiders import BaseCarrierSpider
from crawler.core_carrier.request_helpers import RequestOption
from crawler.core_carrier.rules import RuleManager, BaseRoutingRule
from crawler.core_carrier.items import (
    BaseCarrierItem,
    ExportErrorData,
    MblItem,
    LocationItem,
    VesselItem,
    ContainerItem,
    ContainerStatusItem,
    DebugItem,
)
from crawler.core_carrier.exceptions import (
    CarrierResponseFormatError,
    SuspiciousOperationError,
)
from crawler.core_carrier.base import CARRIER_RESULT_STATUS_ERROR
from crawler.extractors.table_extractors import HeaderMismatchError, BaseTableLocator
from crawler.services.captcha_service import CaptchaSolverService

SITC_BASE_URL = "https://api.sitcline.com/"


class CarrierSitcSpider(BaseCarrierSpider):
    name = "carrier_sitc"

    def __init__(self, *args, **kwargs):
        super(CarrierSitcSpider, self).__init__(*args, **kwargs)

        rules = [
            CaptchaRoutingRule(),
            BasicInfoRoutingRule(),
            ContainerStatusRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)

    def start(self):
        request_option = CaptchaRoutingRule.build_request_option(mbl_no=self.mbl_no,)
        yield self._build_request_by(option=request_option)

    def parse(self, response):
        yield DebugItem(info={"meta": dict(response.meta)})

        routing_rule = self._rule_manager.get_rule_by_response(response=response)

        for result in routing_rule.handle(response=response):
            if isinstance(result, BaseCarrierItem):
                yield result
            elif isinstance(result, RequestOption):
                yield self._build_request_by(option=result)
            else:
                raise RuntimeError()

    def _build_request_by(self, option: RequestOption):
        meta = {RuleManager.META_CARRIER_CORE_RULE_NAME: option.rule_name, **option.meta}

        if option.method == RequestOption.METHOD_GET:
            return scrapy.Request(url=option.url, meta=meta,)
        elif option.method == RequestOption.METHOD_POST_FORM:
            return scrapy.FormRequest(url=option.url, formdata=option.form_data, meta=meta,)
        elif option.method == RequestOption.METHOD_POST_BODY:
            return scrapy.Request(method="POST", url=option.url, headers=option.headers, body=option.body, meta=meta,)
        else:
            raise SuspiciousOperationError(msg=f"Unexpected request method: `{option.method}`")


# -------------------------------------------------------------------------------
class CaptchaRoutingRule(BaseRoutingRule):
    name = "CAPTCHA"

    @classmethod
    def build_request_option(cls, mbl_no) -> RequestOption:
        rand_str = "".join(random.choice(string.digits) for _ in range(17))

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=f"{SITC_BASE_URL}/code?randomStr={rand_str}",
            headers={"Content-Type": "application/text"},
            meta={"mbl_no": mbl_no, "rand_str": rand_str,},
        )

    def handle(self, response):
        mbl_no = response.meta["mbl_no"]
        rand_str = response.meta["rand_str"]
        captcha_solver = CaptchaSolverService()
        captcha_code = captcha_solver.solve_image(image_content=response.body)

        yield BasicInfoRoutingRule.build_request_option(mbl_no=mbl_no, rand_str=rand_str, captcha_code=captcha_code)


class BasicInfoRoutingRule(BaseRoutingRule):
    name = "BASIC_INFO"

    @classmethod
    def build_request_option(cls, mbl_no: str, rand_str: str, captcha_code: str) -> RequestOption:
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_POST_BODY,
            url=f"{SITC_BASE_URL}/doc/cargoTrack/search?blNo={mbl_no}&containerNo=&code={captcha_code}&randomStr={rand_str}",
            headers={"Content-Type": "application/json"},
            meta={"mbl_no": mbl_no,},
        )

    def get_save_name(self, response) -> str:
        return f"{self.name}.json"

    def handle(self, response):
        mbl_no = response.meta["mbl_no"]
        response_dict = json.loads(response.text)["data"]

        basic_info = self._extract_basic_info(response=response_dict)
        if basic_info:
            yield MblItem(
                mbl_no=basic_info["mbl_no"],
                pol=LocationItem(name=basic_info["pol_name"]),
                final_dest=LocationItem(name=basic_info["final_dest_name"]),
            )
        else:
            yield ExportErrorData(mbl_no=mbl_no, status=CARRIER_RESULT_STATUS_ERROR, detail="Data was not found")

        vessel_info_list = self._extract_vessel_info_list(response=response_dict)
        for vessel in vessel_info_list:
            vessel_name = vessel["vessel"]
            yield VesselItem(
                vessel_key=vessel_name,
                vessel=vessel_name,
                voyage=vessel["voyage"],
                pol=LocationItem(name=vessel["pol_name"]),
                pod=LocationItem(name=vessel["pod_name"]),
                etd=vessel["etd"] or None,
                atd=vessel["atd"] or None,
                eta=vessel["eta"] or None,
                ata=vessel["ata"] or None,
            )

        container_info_list = self._extract_container_info_list(response=response_dict)
        for container in container_info_list:
            container_no = container["container_no"]
            yield ContainerItem(
                container_key=container_no, container_no=container_no,
            )

            yield ContainerStatusRoutingRule.build_request_option(mbl_no=mbl_no, container_no=container_no)

    @staticmethod
    def _extract_basic_info(response: Dict) -> Dict:
        basic_list = response["list1"]

        if len(basic_list) != 1:
            return {}

        basic_info = basic_list[0]
        return {
            "mbl_no": basic_info["blNo"],
            "pol_name": basic_info["pol"],
            "final_dest_name": basic_info["del"],
        }

    @staticmethod
    def _extract_vessel_info_list(response: Dict) -> List:
        response_list = response["list2"]

        vessel_info_list = []
        for vessel in response_list:
            vessel_info_list.append(
                {
                    "vessel": vessel["vesselName"],
                    "voyage": vessel["voyageNo"],
                    "pol_name": vessel["portFromName"],
                    "pod_name": vessel["portToName"],
                    "etd": vessel["etd"],
                    "atd": vessel["atd"],
                    "eta": vessel["eta"],
                    "ata": vessel["ata"],
                }
            )

        return vessel_info_list

    @staticmethod
    def _extract_estimate_and_actual_time(vessel_time) -> Dict:
        patt = re.compile(r'^<font color="(?P<e_or_a>\w+)">(?P<local_date_time>\d{4}-\d{2}-\d{2} \d{2}:\d{2})</font>$')
        m = patt.match(vessel_time)
        if not m:
            raise CarrierResponseFormatError(reason=f"time not match, vessel_time: {vessel_time}")

        e_or_a = m.group("e_or_a")
        local_date_time = m.group("local_date_time")

        if e_or_a == "red":
            return {
                "e_time": "",
                "a_time": local_date_time,
            }

        elif e_or_a == "black":
            return {
                "e_time": local_date_time,
                "a_time": "",
            }

        else:
            raise CarrierResponseFormatError(reason=f"unknown e_or_a: `{e_or_a}`")

    @staticmethod
    def _extract_container_info_list(response: Dict) -> List:
        container_list = response["list3"]

        return_list = []
        for container in container_list:
            return_list.append(
                {"container_no": container["containerNo"],}
            )

        return return_list


class ContainerStatusRoutingRule(BaseRoutingRule):
    name = "CONTAINER_STATUS"

    @classmethod
    def build_request_option(cls, mbl_no: str, container_no: str) -> RequestOption:
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_POST_BODY,
            url=f"{SITC_BASE_URL}/doc/cargoTrack/detail?blNo={mbl_no}&containerNo={container_no}",
            headers={"Content-Type": "application/json"},
            meta={"container_key": container_no},
        )

    def get_save_name(self, response) -> str:
        container_key = response.meta["container_key"]
        return f"{self.name}_{container_key}.html"

    def handle(self, response):
        container_key = response.meta["container_key"]
        response_dict = json.loads(response.text)["data"]

        container_status_list = self._extract_container_status_list(response=response_dict)
        for container_status in container_status_list:
            yield ContainerStatusItem(
                container_key=container_key,
                description=container_status["description"],
                local_date_time=container_status["local_date_time"],
                location=LocationItem(name=container_status["location_name"]),
            )

    @staticmethod
    def _extract_container_status_list(response: dict) -> List:
        response_list = response["list"]

        container_status_list = []
        for item in response_list:
            container_status_list.append(
                {
                    "local_date_time": item["eventdate"],  # Occurence Time
                    "description": item["movementnameen"],  # Current Status
                    "location_name": item["portname"],  # Local
                }
            )

        return container_status_list


class ContainerStatusTableLocator(BaseTableLocator):

    TR_TITLE_INDEX = 0

    def __init__(self):
        self._td_map = {}
        self._data_len = 0

    def parse(self, table: scrapy.Selector):
        title_tr = table.css("thead tr")[self.TR_TITLE_INDEX]
        data_tr_list = table.css("tbody tr")

        title_text_list = title_tr.css("td::text").getall()

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
