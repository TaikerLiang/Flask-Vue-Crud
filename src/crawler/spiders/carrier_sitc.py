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
from crawler.services.captcha_service import CaptchaSolverService

SITC_BASE_URL = "https://api.sitcline.com"


class CarrierSitcSpider(BaseCarrierSpider):
    name = "carrier_sitc"

    handle_httpstatus_list = [428, 502]
    max_428_502_error_retry_times = 3

    def __init__(self, *args, **kwargs):
        super(CarrierSitcSpider, self).__init__(*args, **kwargs)

        rules = [
            Captcha1RoutingRule(),
            LoginRoutingRule(),
            Captcha2RoutingRule(),
            BasicInfoRoutingRule(),
            ContainerStatusRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)

    def start(self):
        request_option = Captcha1RoutingRule.build_request_option(
            mbl_no=self.mbl_no,
        )
        yield self._build_request_by(option=request_option)

    def parse(self, response):
        yield DebugItem(info={"meta": dict(response.meta)})

        routing_rule = self._rule_manager.get_rule_by_response(response=response)

        if response.status in CarrierSitcSpider.handle_httpstatus_list and self.max_428_502_error_retry_times != 0:
            yield DebugItem(info=f"{response.status} error, remaining retry times {self.max_428_502_error_retry_times}")

            self.max_428_502_error_retry_times -= 1
            for request in self.start():
                yield request

            return

        if routing_rule.name != "CAPTCHA1" and routing_rule.name != "CAPTCHA2":
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
        meta = {RuleManager.META_CARRIER_CORE_RULE_NAME: option.rule_name, **option.meta}

        if option.method == RequestOption.METHOD_GET:
            return scrapy.Request(url=option.url, meta=meta, headers=option.headers)
        elif option.method == RequestOption.METHOD_POST_FORM:
            return scrapy.FormRequest(
                url=option.url,
                formdata=option.form_data,
                meta=meta,
            )
        elif option.method == RequestOption.METHOD_POST_BODY:
            return scrapy.Request(
                method="POST",
                url=option.url,
                headers=option.headers,
                body=option.body,
                meta=meta,
            )
        else:
            raise SuspiciousOperationError(msg=f"Unexpected request method: `{option.method}`")


# -------------------------------------------------------------------------------
class Captcha1RoutingRule(BaseRoutingRule):
    name = "CAPTCHA1"

    @classmethod
    def build_request_option(cls, mbl_no) -> RequestOption:
        rand_str = "".join(random.choice(string.digits) for _ in range(17))

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=f"{SITC_BASE_URL}/code?randomStr={rand_str}",
            headers={"Content-Type": "application/text"},
            meta={
                "mbl_no": mbl_no,
                "rand_str": rand_str,
            },
        )

    def handle(self, response):
        mbl_no = response.meta["mbl_no"]
        rand_str = response.meta["rand_str"]
        captcha_solver = CaptchaSolverService()
        captcha_code = captcha_solver.solve_image(image_content=response.body)

        yield LoginRoutingRule.build_request_option(mbl_no=mbl_no, rand_str=rand_str, captcha_code=captcha_code)


# -------------------------------------------------------------------------------


class LoginRoutingRule(BaseRoutingRule):
    name = "LOGIN"
    USERNAME = "GoFreight"
    PASSWORD = "hardcore@2021"

    @classmethod
    def build_request_option(cls, mbl_no: str, rand_str: str, captcha_code: str) -> RequestOption:
        url = (
            f"{SITC_BASE_URL}/auth/oauth/token?username={cls.USERNAME}&password=mnKt%2B%2BJ6mBIizkv7%2BhnfyQ%3D%3D"
            f"&randomStr={rand_str}&code={captcha_code}&grant_type=password&scope=server"
        )

        return RequestOption(
            method=RequestOption.METHOD_GET,
            rule_name=cls.name,
            url=url,
            headers={"Accept": "application/json", "TenantId": "2", "authorization": "Basic cGlnOnBpZw=="},
            meta={
                "mbl_no": mbl_no,
            },
        )

    def get_save_name(self, response) -> str:
        return f"{self.name}.json"

    def handle(self, response):
        mbl_no = response.meta["mbl_no"]
        response_dict = json.loads(response.text)
        token = f"{response_dict['token_type']} {response_dict['access_token']}"
        yield DebugItem(info=f"token: {token}")

        yield Captcha2RoutingRule.build_request_option(mbl_no=mbl_no, token=token)


# -------------------------------------------------------------------------------


class Captcha2RoutingRule(BaseRoutingRule):
    name = "CAPTCHA2"

    @classmethod
    def build_request_option(cls, mbl_no, token: str) -> RequestOption:
        rand_str = "".join(random.choice(string.digits) for _ in range(17))

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=f"{SITC_BASE_URL}/code?randomStr={rand_str}",
            headers={"Content-Type": "application/text"},
            meta={"mbl_no": mbl_no, "rand_str": rand_str, "token": token},
        )

    def handle(self, response):
        mbl_no = response.meta["mbl_no"]
        rand_str = response.meta["rand_str"]
        token = response.meta["token"]
        captcha_solver = CaptchaSolverService()
        captcha_code = captcha_solver.solve_image(image_content=response.body)

        yield BasicInfoRoutingRule.build_request_option(
            mbl_no=mbl_no, rand_str=rand_str, captcha_code=captcha_code, token=token
        )


class BasicInfoRoutingRule(BaseRoutingRule):
    name = "BASIC_INFO"

    @classmethod
    def build_request_option(cls, mbl_no: str, rand_str: str, captcha_code: str, token: str) -> RequestOption:
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=f"{SITC_BASE_URL}/doc/cargoTrack/search?blNo={mbl_no}&containerNo=&code={captcha_code}&randomStr={rand_str}",
            meta={"mbl_no": mbl_no, "token": token},
        )

    def get_save_name(self, response) -> str:
        return f"{self.name}.json"

    def handle(self, response):
        mbl_no = response.meta["mbl_no"]
        token = response.meta["token"]
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
                container_key=container_no,
                container_no=container_no,
            )

            yield ContainerStatusRoutingRule.build_request_option(mbl_no=mbl_no, container_no=container_no, token=token)

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
                {
                    "container_no": container["containerNo"],
                }
            )

        return return_list


class ContainerStatusRoutingRule(BaseRoutingRule):
    name = "CONTAINER_STATUS"

    @classmethod
    def build_request_option(cls, mbl_no: str, container_no: str, token: str) -> RequestOption:
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_POST_BODY,
            url=f"{SITC_BASE_URL}/doc/cargoTrack/detail?blNo={mbl_no}&containerNo={container_no}",
            headers={
                "Content-Type": "application/json",
                "authorization": token,
                "TenantId": "2",
            },
            meta={"container_key": container_no},
        )

    def get_save_name(self, response) -> str:
        container_key = response.meta["container_key"]
        return f"{self.name}_{container_key}.json"

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
