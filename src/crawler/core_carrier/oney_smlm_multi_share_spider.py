import dataclasses
import json
import time
from typing import Dict, List, Set

import scrapy

from crawler.core.exceptions import ProxyMaxRetryError
from crawler.core.proxy import HydraproxyProxyManager
from crawler.core_carrier.base import (
    CARRIER_RESULT_STATUS_ERROR,
    SHIPMENT_TYPE_BOOKING,
    SHIPMENT_TYPE_MBL,
)
from crawler.core_carrier.base_spiders import BaseMultiCarrierSpider
from crawler.core_carrier.exceptions import (
    CarrierResponseFormatError,
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
    VesselItem,
)
from crawler.core_carrier.request_helpers import RequestOption
from crawler.core_carrier.rules import BaseRoutingRule, RuleManager

MAX_PAGE_NUM = 10
MAX_RETRY_COUNT = 3


@dataclasses.dataclass
class Restart:
    search_nos: list
    task_ids: list
    reason: str = ""


class OneySmlmSharedSpider(BaseMultiCarrierSpider):
    name = None
    base_url = None
    custom_settings = {
        **BaseMultiCarrierSpider.custom_settings,  # type: ignore
        "CONCURRENT_REQUESTS": "1",
    }

    def __init__(self, *args, **kwargs):
        super(OneySmlmSharedSpider, self).__init__(*args, **kwargs)

        self._proxy_manager = HydraproxyProxyManager(session="oneysmlm", logger=self.logger)
        self._retry_count = 0

        bill_rules = [
            FirstTierRoutingRule(search_type=SHIPMENT_TYPE_MBL),
            VesselRoutingRule(),
            ContainerStatusRoutingRule(),
            ReleaseStatusRoutingRule(),
            RailInfoRoutingRule(),
            NextRoundRoutingRule(),
        ]

        booking_rules = [
            FirstTierRoutingRule(search_type=SHIPMENT_TYPE_BOOKING),
            VesselRoutingRule(),
            ContainerStatusRoutingRule(),
            ReleaseStatusRoutingRule(),
            RailInfoRoutingRule(),
            NextRoundRoutingRule(),
        ]

        if self.search_type == SHIPMENT_TYPE_MBL:
            self._rule_manager = RuleManager(rules=bill_rules)
        elif self.search_type == SHIPMENT_TYPE_BOOKING:
            self._rule_manager = RuleManager(rules=booking_rules)

    def start(self):
        self._proxy_manager.renew_proxy()
        option = FirstTierRoutingRule.build_request_option(
            search_nos=self.search_nos, task_ids=self.task_ids, base_url=self.base_url
        )
        yield self._build_request_by(option=option)

    def parse(self, response):
        yield DebugItem(info={"meta": dict(response.meta)})

        routing_rule = self._rule_manager.get_rule_by_response(response=response)

        save_name = routing_rule.get_save_name(response=response)
        self._saver.save(to=save_name, text=response.text)

        for result in routing_rule.handle(response=response):
            if isinstance(result, BaseCarrierItem):
                yield result
            elif isinstance(result, RequestOption):
                if result.rule_name == "NEXT_ROUND":
                    self._retry_count = 0

                proxy_option = self._proxy_manager.apply_proxy_to_request_option(result)
                yield self._build_request_by(option=proxy_option)
            elif isinstance(result, Restart):
                search_nos = result.search_nos
                task_ids = result.task_ids

                if self._retry_count > MAX_RETRY_COUNT:
                    for search_no, task_id in zip(search_nos[:MAX_PAGE_NUM], task_ids[:MAX_PAGE_NUM]):
                        if self.search_type == SHIPMENT_TYPE_MBL:
                            yield ExportErrorData(
                                mbl_no=search_no,
                                task_id=task_id,
                                status=CARRIER_RESULT_STATUS_ERROR,
                                detail="Data was not found",
                            )
                        elif self.search_type == SHIPMENT_TYPE_BOOKING:
                            yield ExportErrorData(
                                mbl_no=search_no,
                                task_id=task_id,
                                status=CARRIER_RESULT_STATUS_ERROR,
                                detail="Data was not found",
                            )

                    option = NextRoundRoutingRule.build_request_option(
                        search_nos=search_nos, task_ids=task_ids, base_url=self.base_url
                    )
                    proxy_option = self._proxy_manager.apply_proxy_to_request_option(option)
                    yield self._build_request_by(proxy_option)
                    return

                self._retry_count += 1
                self.logger.warning(f"----- {result.reason}, try new proxy and restart")

                try:
                    self._proxy_manager.renew_proxy()
                except ProxyMaxRetryError:
                    for search_no, task_id in zip(search_nos, task_ids):
                        if self.search_type == SHIPMENT_TYPE_MBL:
                            yield ExportErrorData(
                                mbl_no=search_no,
                                task_id=task_id,
                                status=CARRIER_RESULT_STATUS_ERROR,
                                detail="proxy max retry error",
                            )
                        elif self.search_type == SHIPMENT_TYPE_BOOKING:
                            yield ExportErrorData(
                                mbl_no=search_no,
                                task_id=task_id,
                                status=CARRIER_RESULT_STATUS_ERROR,
                                detail="proxy max retry error",
                            )
                    return

                option = FirstTierRoutingRule.build_request_option(
                    search_nos=search_nos, task_ids=task_ids, base_url=self.base_url
                )
                proxy_option = self._proxy_manager.apply_proxy_to_request_option(option)
                yield self._build_request_by(proxy_option)
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
            raise SuspiciousOperationError(msg=f"Unexpected request method: `{option.method}`")


class FirstTierRoutingRule(BaseRoutingRule):
    name = "FIRST_TIER"
    f_cmd = "121"

    def __init__(self, search_type):
        # aim to build other routing_request
        self._search_type = search_type

    @classmethod
    def build_request_option(cls, search_nos, base_url, task_ids) -> RequestOption:
        time_stamp = build_timestamp()
        if len(search_nos) > MAX_PAGE_NUM:
            search_name = ",".join(search_nos[:MAX_PAGE_NUM])
        else:
            search_name = ",".join(search_nos)

        url = (
            f"{base_url}?_search=false&nd={time_stamp}&rows=10000&page=1&sidx=&sord=asc&"
            f"f_cmd={cls.f_cmd}&search_type=B&search_name={search_name}&cust_cd="
        )

        headers = {
            "authority": "ecomm.one-line.com",
            "sec-ch-ua": '" Not A;Brand";v="99", "Chromium";v="90", "Google Chrome";v="90"',
            "accept": "application/json, text/javascript, */*; q=0.01",
            "x-requested-with": "XMLHttpRequest",
            "sec-ch-ua-mobile": "?0",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
            "sec-fetch-site": "same-origin",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
            "referer": "https://ecomm.one-line.com/ecom/CUP_HOM_3301.do?sessLocale=en",
            "accept-language": "en-US,en;q=0.9",
        }

        return RequestOption(
            method=RequestOption.METHOD_GET,
            rule_name=cls.name,
            url=url,
            headers=headers,
            meta={
                "base_url": base_url,
                "task_ids": task_ids,
                "search_nos": search_nos,
            },
        )

    def get_save_name(self, response) -> str:
        return f"{self.name}.json"

    def handle(self, response):
        task_ids = response.meta["task_ids"]
        search_nos = response.meta["search_nos"]
        base_url = response.meta["base_url"]

        if self._is_json_response_invalid(response):
            yield Restart(reason="JSON response invalid", search_nos=search_nos, task_ids=task_ids)
            return

        response_dict = json.loads(response.text)
        if self._is_search_no_invalid(response_dict):
            yield Restart(reason="IP block", search_nos=search_nos, task_ids=task_ids)
            return

        container_info_list = self._extract_container_info_list(response_dict=response_dict)
        booking_no_set = self._get_booking_no_set_from(container_list=container_info_list)
        mbl_no_set = self._get_mbl_no_set_from(container_list=container_info_list)

        if len(search_nos) > MAX_PAGE_NUM:
            search_nos_in_paging = search_nos[:MAX_PAGE_NUM]
            task_ids_in_paging = task_ids[:MAX_PAGE_NUM]
        else:
            search_nos_in_paging = search_nos
            task_ids_in_paging = task_ids

        for search_no, task_id in zip(search_nos_in_paging, task_ids_in_paging):
            if self._search_type == SHIPMENT_TYPE_MBL:
                if search_no in mbl_no_set:
                    final_dest = ""
                    for container in container_info_list:
                        if container["mbl_no"] == search_no:
                            final_dest = container["final_dest"]
                            break

                    yield MblItem(task_id=task_id, mbl_no=search_no, final_dest=LocationItem(name=final_dest))
                    yield VesselRoutingRule.build_request_option(
                        booking_no=search_no, base_url=base_url, task_id=task_id
                    )
                else:
                    # TODO: maybe could refactor later, use DataNotFoundError or CarrierInvalidMblNoError.
                    yield ExportErrorData(
                        task_id=task_id,
                        mbl_no=search_no,
                        status=CARRIER_RESULT_STATUS_ERROR,
                        detail="Data was not found",
                    )
            elif self._search_type == SHIPMENT_TYPE_BOOKING:
                if search_no in booking_no_set:
                    final_dest = ""
                    for container in container_info_list:
                        if container["booking_no"] == search_no:
                            final_dest = container["final_dest"]
                            break

                    yield MblItem(task_id=task_id, booking_no=search_no, final_dest=LocationItem(name=final_dest))
                    yield VesselRoutingRule.build_request_option(
                        booking_no=search_no, base_url=base_url, task_id=task_id
                    )
                else:
                    # TODO: maybe could refactor later, use DataNotFoundError or CarrierInvalidMblNoError.
                    yield ExportErrorData(
                        task_id=task_id,
                        booking_no=search_no,
                        status=CARRIER_RESULT_STATUS_ERROR,
                        detail="Data was not found",
                    )

        for container_info in container_info_list:
            container_no = container_info["container_no"]
            if self._search_type == SHIPMENT_TYPE_MBL:
                search_no = container_info["mbl_no"]
            else:
                search_no = container_info["booking_no"]
            index = search_nos.index(search_no)
            task_id = task_ids[index]

            yield ContainerItem(
                task_id=task_id,
                container_key=container_no,
                container_no=container_no,
            )

            yield ContainerStatusRoutingRule.build_request_option(
                container_no=container_no,
                booking_no=container_info["booking_no"],
                cooperation_no=container_info["cooperation_no"],
                base_url=base_url,
                task_id=task_id,
                search_nos=search_nos,
                task_ids=task_ids,
            )

            yield ReleaseStatusRoutingRule.build_request_option(
                container_no=container_no,
                booking_no=container_info["booking_no"],
                base_url=base_url,
                task_id=task_id,
            )

            yield RailInfoRoutingRule.build_request_option(
                container_no=container_no,
                cooperation=container_info["cooperation_no"],
                base_url=base_url,
                task_id=task_id,
            )

        yield NextRoundRoutingRule.build_request_option(search_nos=search_nos, task_ids=task_ids, base_url=base_url)

    @staticmethod
    def _is_json_response_invalid(response):
        return "System error" in response.text

    def _is_search_no_invalid(self, response_dict: Dict) -> bool:
        return "list" not in response_dict

    def _extract_container_info_list(self, response_dict: Dict) -> List:
        container_data_list = response_dict.get("list")
        if not container_data_list:
            return []

        container_info_list = []
        for container_data in container_data_list:
            mbl_no = container_data["blNo"].strip()
            container_no = container_data["cntrNo"].strip()
            booking_no = container_data["bkgNo"].strip()
            cooperation_no = container_data["copNo"].strip()
            final_dest = container_data["placeNm"].strip()

            container_info_list.append(
                {
                    "mbl_no": mbl_no,
                    "container_no": container_no,
                    "booking_no": booking_no,
                    "cooperation_no": cooperation_no,
                    "final_dest": final_dest,
                }
            )

        return container_info_list

    def _get_booking_no_set_from(self, container_list: List) -> Set:
        booking_no_list = [container["booking_no"] for container in container_list]
        booking_no_set = set(booking_no_list)

        return booking_no_set

    def _get_mbl_no_set_from(self, container_list: List) -> Set:
        mbl_no_list = [container["mbl_no"] for container in container_list]
        mbl_no_set = set(mbl_no_list)

        return mbl_no_set


class VesselRoutingRule(BaseRoutingRule):
    name = "VESSEL"
    f_cmd = "124"

    @classmethod
    def build_request_option(cls, booking_no, base_url, task_id) -> RequestOption:
        form_data = {
            "f_cmd": cls.f_cmd,
            "bkg_no": booking_no,
        }

        return RequestOption(
            method=RequestOption.METHOD_POST_FORM,
            rule_name=cls.name,
            url=base_url,
            form_data=form_data,
            meta={
                "task_id": task_id,
            },
        )

    def get_save_name(self, response) -> str:
        return f"{self.name}.json"

    def handle(self, response):
        task_id = response.meta["task_id"]
        response_dict = json.loads(response.text)

        if self._is_vessel_empty(response_dict=response_dict):
            return
            yield VesselItem(vessel_key="", task_id=task_id)

        vessel_info_list = self._extract_vessel_info_list(response_dict=response_dict)
        for vessel_info in vessel_info_list:
            yield VesselItem(
                task_id=task_id,
                vessel_key=vessel_info.get("name", ""),
                vessel=vessel_info.get("name", ""),
                voyage=vessel_info.get("voyage", ""),
                pol=LocationItem(name=vessel_info.get("pol", "")),
                pod=LocationItem(name=vessel_info.get("pod", "")),
                etd=vessel_info.get("etd", ""),
                atd=vessel_info.get("atd", ""),
                eta=vessel_info.get("eta", ""),
                ata=vessel_info.get("ata", ""),
            )

    def _is_vessel_empty(self, response_dict: Dict) -> List:
        return "list" not in response_dict

    def _extract_vessel_info_list(self, response_dict: Dict) -> List:
        vessel_data_list = response_dict["list"]
        vessel_info_list = []
        for vessel_data in vessel_data_list:
            vessel_info_list.append(
                {
                    "name": vessel_data.get("vslEngNm", "").strip(),
                    "voyage": vessel_data.get("skdVoyNo", "").strip() + vessel_data["skdDirCd"].strip(),
                    "pol": vessel_data.get("polNm", "").strip(),
                    "pod": vessel_data.get("podNm", "").strip(),
                    "etd": vessel_data.get("etd", "").strip() if vessel_data["etdFlag"] == "C" else None,
                    "atd": vessel_data.get("etd", "").strip() if vessel_data["etdFlag"] == "A" else None,
                    "eta": vessel_data.get("eta", "").strip() if vessel_data["etaFlag"] == "C" else None,
                    "ata": vessel_data.get("eta", "").strip() if vessel_data["etaFlag"] == "A" else None,
                }
            )

        return vessel_info_list


class ContainerStatusRoutingRule(BaseRoutingRule):
    name = "CONTAINER_STATUS"
    f_cmd = "125"

    @classmethod
    def build_request_option(
        cls, container_no, booking_no, cooperation_no, base_url, task_id, search_nos, task_ids
    ) -> RequestOption:
        form_data = {
            "f_cmd": cls.f_cmd,
            "cntr_no": container_no,
            "bkg_no": booking_no,
            "cop_no": cooperation_no,
        }

        return RequestOption(
            method=RequestOption.METHOD_POST_FORM,
            rule_name=cls.name,
            url=base_url,
            form_data=form_data,
            meta={
                "container_key": container_no,
                "task_id": task_id,
                "search_nos": search_nos,
                "task_ids": task_ids,
            },
        )

    def get_save_name(self, response) -> str:
        container_key = response.meta["container_key"]
        return f"{self.name}_{container_key}.json"

    def handle(self, response):
        task_id = response.meta["task_id"]
        container_key = response.meta["container_key"]
        task_ids = response.meta["task_ids"]
        search_nos = response.meta["search_nos"]

        response_dict = json.loads(response.text)

        container_status_list = self._extract_container_status_list(response_dict=response_dict)

        if not container_status_list:
            yield Restart(reason="No container status info", search_nos=search_nos, task_ids=task_ids)
            return

        for container_status in container_status_list:
            yield ContainerStatusItem(
                task_id=task_id,
                container_key=container_key,
                description=container_status["status"],
                local_date_time=container_status["local_time"],
                location=LocationItem(name=container_status["location"]),
                est_or_actual=container_status["est_or_actual"],
            )

    def _extract_container_status_list(self, response_dict: Dict) -> List:
        if "list" not in response_dict:
            return []

        container_status_data_list = response_dict["list"]
        container_status_info_list = []
        for container_status_data in container_status_data_list:
            local_time = container_status_data["eventDt"].strip()
            if not local_time:
                # time is empty --> ignore this event
                continue

            status_with_br = container_status_data["statusNm"].strip()
            status = status_with_br.replace("<br>", " ")

            container_status_info_list.append(
                {
                    "status": status,
                    "location": container_status_data["placeNm"].strip(),
                    "local_time": local_time,
                    "est_or_actual": container_status_data["actTpCd"].strip(),
                }
            )

        return container_status_info_list


class ReleaseStatusRoutingRule(BaseRoutingRule):
    name = "RELEASE_STATUS"
    f_cmd = "126"

    @classmethod
    def build_request_option(cls, container_no, booking_no, base_url, task_id) -> RequestOption:
        form_data = {
            "f_cmd": cls.f_cmd,
            "cntr_no": container_no,
            "bkg_no": booking_no,
        }

        return RequestOption(
            method=RequestOption.METHOD_POST_FORM,
            rule_name=cls.name,
            url=base_url,
            form_data=form_data,
            meta={
                "container_key": container_no,
                "task_id": task_id,
            },
        )

    def get_save_name(self, response) -> str:
        container_key = response.meta["container_key"]
        return f"{self.name}_{container_key}.json"

    def handle(self, response):
        task_id = response.meta["task_id"]
        container_key = response.meta["container_key"]
        response_dict = json.loads(response.text)

        release_info = self._extract_release_info(response_dict=response_dict)

        yield MblItem(
            task_id=task_id,
            freight_date=release_info.get("freight_date") or None,
            us_customs_date=release_info.get("us_customs_date") or None,
            us_filing_date=release_info.get("us_filing_date") or None,
            firms_code=release_info.get("firms_code") or None,
        )

        yield ContainerItem(
            task_id=task_id,
            container_key=container_key,
            last_free_day=release_info.get("last_free_day") or None,
            terminal_pod=LocationItem(name=release_info.get("terminal") or None),
        )

    def _extract_release_info(self, response_dict: Dict) -> Dict:
        if "list" not in response_dict:
            return {}

        release_data_list = response_dict["list"]
        if len(release_data_list) != 1:
            raise CarrierResponseFormatError(reason=f"Release information format error: `{release_data_list}`")

        release_data = release_data_list[0]

        return {
            "freight_date": release_data["ocnFrtColDt"],
            "us_customs_date": release_data["cstmsClrDt"],
            "us_filing_date": release_data["impFilDt"],
            "firms_code": release_data["delFirmsCode"],
            "last_free_day": release_data["lastFreeDt"],
            "terminal": release_data["podFirmsCode"],
        }


class RailInfoRoutingRule(BaseRoutingRule):
    name = "RAIL_INFORMATION"
    f_cmd = "127"

    @classmethod
    def build_request_option(cls, container_no, cooperation, base_url, task_id) -> RequestOption:
        form_data = {
            "f_cmd": cls.f_cmd,
            "cop_no": cooperation,
        }

        return RequestOption(
            method=RequestOption.METHOD_POST_FORM,
            rule_name=cls.name,
            url=base_url,
            form_data=form_data,
            meta={
                "container_key": container_no,
                "task_id": task_id,
            },
        )

    def get_save_name(self, response) -> str:
        container_key = response.meta["container_key"]
        return f"{self.name}_{container_key}.json"

    def handle(self, response):
        task_id = response.meta["task_id"]
        container_key = response.meta["container_key"]
        response_dict = json.loads(response.text)

        rail_info = self._extract_rail_info(response_dict=response_dict)

        yield ContainerItem(
            task_id=task_id,
            container_key=container_key,
            ready_for_pick_up=rail_info.get("ready_for_pick_up", "") or None,
            railway=rail_info.get("railway") or None,
            final_dest_eta=rail_info.get("final_dest_eta", "") or None,
        )

    def _extract_rail_info(self, response_dict: Dict) -> Dict:
        if "list" not in response_dict:
            return {}

        rail_data_list = response_dict["list"]
        if len(rail_data_list) != 1:
            raise CarrierResponseFormatError(reason=f"Rail information format error: `{rail_data_list}`")

        rail_data = rail_data_list[0]

        return {
            "ready_for_pick_up": rail_data["pickUpAvail"],
            "railway": rail_data["inArrYardNm"],
            "final_dest_eta": rail_data["inArrDate"],
        }


class NextRoundRoutingRule(BaseRoutingRule):
    name = "NEXT_ROUND"

    @classmethod
    def build_request_option(cls, search_nos: List, task_ids: List, base_url: str) -> RequestOption:
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url="https://eval.edi.hardcoretech.co/c/livez",
            meta={"search_nos": search_nos, "task_ids": task_ids, "base_url": base_url},
        )

    def handle(self, response):
        task_ids = response.meta["task_ids"]
        search_nos = response.meta["search_nos"]
        base_url = response.meta["base_url"]

        if len(search_nos) <= MAX_PAGE_NUM and len(task_ids) <= MAX_PAGE_NUM:
            return

        task_ids = task_ids[MAX_PAGE_NUM:]
        search_nos = search_nos[MAX_PAGE_NUM:]

        yield FirstTierRoutingRule.build_request_option(search_nos=search_nos, task_ids=task_ids, base_url=base_url)


# -----------------------------------------------------------------------------------------------------------


def build_timestamp():
    return int(time.time() * 1000)
