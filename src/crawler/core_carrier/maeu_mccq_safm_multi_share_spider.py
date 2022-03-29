import json
from typing import Dict, List, Tuple

import scrapy

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
)
from crawler.core_carrier.request_helpers import RequestOption
from crawler.core_carrier.rules import BaseRoutingRule, RuleManager


class MaeuMccqSafmShareSpider(BaseMultiCarrierSpider):
    name = ""
    base_url_format = ""
    custom_settings = {
        **BaseMultiCarrierSpider.custom_settings,  # type: ignore
        "CONCURRENT_REQUESTS": "1",
    }

    def __init__(self, *args, **kwargs):
        super(MaeuMccqSafmShareSpider, self).__init__(*args, **kwargs)

        bill_rules = [
            MainInfoRoutingRule(SHIPMENT_TYPE_MBL),
            NextRoundRoutingRule(),
        ]

        booking_rules = [
            MainInfoRoutingRule(SHIPMENT_TYPE_BOOKING),
            NextRoundRoutingRule(),
        ]

        self._proxy_manager = HydraproxyProxyManager(session="maeu_mccq_safm_share", logger=self.logger)
        if self.search_type == SHIPMENT_TYPE_MBL:
            self._rule_manager = RuleManager(rules=bill_rules)
        elif self.search_type == SHIPMENT_TYPE_BOOKING:
            self._rule_manager = RuleManager(rules=booking_rules)

    def start(self):
        option = MainInfoRoutingRule.build_request_option(
            search_nos=self.search_nos, task_ids=self.task_ids, url_format=self.base_url_format
        )

        self._proxy_manager.renew_proxy()
        proxy_option = self._proxy_manager.apply_proxy_to_request_option(option=option)
        yield self._build_request_by(option=proxy_option)

    def parse(self, response):
        yield DebugItem(info={"meta": dict(response.meta)})

        routing_rule = self._rule_manager.get_rule_by_response(response=response)
        if routing_rule.name != "ROUTING":
            save_name = routing_rule.get_save_name(response=response)
            self._saver.save(to=save_name, text=response.text)

        for result in routing_rule.handle(response=response):
            if isinstance(result, BaseCarrierItem):
                yield result
            elif isinstance(result, RequestOption):
                if response.meta[RuleManager.META_CARRIER_CORE_RULE_NAME] == NextRoundRoutingRule.name:
                    self._proxy_manager.renew_proxy()
                    result = self._proxy_manager.apply_proxy_to_request_option(option=result)

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
        else:
            raise SuspiciousOperationError(msg=f"Unexpected request method: `{option.method}`")


class MainInfoRoutingRule(BaseRoutingRule):
    name = "MAIN_INFO"

    def __init__(self, search_type):
        self._search_type = search_type

    @classmethod
    def build_request_option(cls, search_nos: List, task_ids: List, url_format: str) -> RequestOption:
        if search_nos[0][:4] == "SEAU":
            seau_url_format = url_format[:-4] + "seau"
            url = seau_url_format.format(search_no=search_nos[0][4:])
        # More special case could be added here
        else:
            url = url_format.format(search_no=search_nos[0])

        return RequestOption(
            method=RequestOption.METHOD_GET,
            rule_name=cls.name,
            url=url,
            meta={
                "task_ids": task_ids,
                "search_nos": search_nos,
                "url_format": url_format,
                "handle_httpstatus_list": [400, 404],
            },
        )

    def get_save_name(self, response) -> str:
        return f"{self.name}.json"

    def handle(self, response):
        task_ids = response.meta["task_ids"]
        search_nos = response.meta["search_nos"]
        url_format = response.meta["url_format"]

        current_task_id = task_ids[0]
        response_dict = json.loads(response.text)

        if self.is_search_no_invalid(response_dict):
            if self._search_type == SHIPMENT_TYPE_MBL:
                yield ExportErrorData(
                    task_id=current_task_id,
                    mbl_no=search_nos[0],
                    status=CARRIER_RESULT_STATUS_ERROR,
                    detail="Data was not found",
                )
                yield NextRoundRoutingRule.build_request_option(
                    search_nos=search_nos, task_ids=task_ids, url_format=url_format
                )
                return
            else:
                yield ExportErrorData(
                    task_id=current_task_id,
                    booking_no=search_nos[0],
                    status=CARRIER_RESULT_STATUS_ERROR,
                    detail="Data was not found",
                )
                yield NextRoundRoutingRule.build_request_option(
                    search_nos=search_nos, task_ids=task_ids, url_format=url_format
                )
                return

        search_no = self._extract_search_no(response_dict=response_dict)
        routing_info = self._extract_routing_info(response_dict=response_dict)

        mbl_item = MblItem(
            task_id=current_task_id,
            por=LocationItem(name=routing_info["por"]),
            final_dest=LocationItem(name=routing_info["final_dest"]),
        )
        if self._search_type == SHIPMENT_TYPE_MBL:
            mbl_item["mbl_no"] = search_no
        else:
            mbl_item["booking_no"] = search_no
        yield mbl_item

        containers = self._extract_containers(response_dict=response_dict)
        for container in containers:
            container_no = container["no"]

            yield ContainerItem(
                task_id=current_task_id,
                container_key=container_no,
                container_no=container_no,
                final_dest_eta=container["final_dest_eta"],
            )

            for container_status in container["container_statuses"]:
                yield ContainerStatusItem(
                    task_id=current_task_id,
                    container_key=container_no,
                    description=container_status["description"],
                    local_date_time=container_status["timestamp"],
                    location=LocationItem(name=container_status["location_name"]),
                    vessel=container_status["vessel"] or None,
                    voyage=container_status["voyage"] or None,
                    est_or_actual=container_status["est_or_actual"],
                )

        yield NextRoundRoutingRule.build_request_option(search_nos=search_nos, task_ids=task_ids, url_format=url_format)

    @staticmethod
    def is_search_no_invalid(response_dict):
        if "error" in response_dict:
            return True
        return False

    @staticmethod
    def _extract_search_no(response_dict):
        return response_dict["tpdoc_num"]

    def _extract_routing_info(self, response_dict):
        origin = response_dict["origin"]
        destination = response_dict.get("destination")

        return {
            "por": self._format_location(loc_info=origin),
            "final_dest": self._format_location(loc_info=destination) if destination else None,
        }

    def _extract_containers(self, response_dict):
        containers = response_dict["containers"]

        container_info_list = []
        for container in containers:
            container_statuses = []

            locations = container.get("locations", [])
            for location in locations:
                location_name = self._format_location(loc_info=location)

                for event in location["events"]:
                    timestamp, est_or_actual = self._get_time_and_status(event)

                    container_statuses.append(
                        {
                            "location_name": location_name,
                            "description": event["activity"],
                            "vessel": self._format_vessel_name(
                                vessel_name=event["vessel_name"], vessel_num=event["vessel_num"]
                            ),
                            "voyage": event["voyage_num"],
                            "timestamp": timestamp,
                            "est_or_actual": est_or_actual,
                        }
                    )

            container_info_list.append(
                {
                    "no": container["container_num"],
                    "final_dest_eta": container["eta_final_delivery"],
                    "container_statuses": container_statuses,
                }
            )

        return container_info_list

    @staticmethod
    def _format_location(loc_info: Dict):
        # terminal
        if loc_info["terminal"]:
            terminal_str = f"{loc_info['terminal']} -- "
        else:
            terminal_str = ""

        # state & country
        state_country_list = []

        if loc_info["state"]:
            state_country_list.append(loc_info["state"])

        state_country_list.append(loc_info["country_code"])
        state_country_str = ", ".join(state_country_list)

        return f"{terminal_str}{loc_info['city']} ({state_country_str})"

    @staticmethod
    def _format_vessel_name(vessel_name, vessel_num):
        name_list = []

        if vessel_name:
            name_list.append(vessel_name)

        if vessel_num:
            name_list.append(vessel_num)

        return " ".join(name_list)

    @staticmethod
    def _get_time_and_status(event: Dict) -> Tuple:
        if "actual_time" in event:
            return event["actual_time"], "A"

        if "expected_time" in event:
            return event["expected_time"], "E"

        raise CarrierResponseFormatError(reason=f"Unknown time in container_status `{event}`")


class NextRoundRoutingRule(BaseRoutingRule):
    name = "ROUTING"

    @classmethod
    def build_request_option(cls, search_nos: List, task_ids: List, url_format: str) -> RequestOption:
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url="https://eval.edi.hardcoretech.co/c/livez",
            meta={
                "search_nos": search_nos,
                "task_ids": task_ids,
                "url_format": url_format,
            },
        )

    def handle(self, response):
        task_ids = response.meta["task_ids"]
        search_nos = response.meta["search_nos"]
        url_format = response.meta["url_format"]

        if len(search_nos) == 1 and len(task_ids) == 1:
            return

        task_ids = task_ids[1:]
        search_nos = search_nos[1:]

        yield MainInfoRoutingRule.build_request_option(search_nos=search_nos, task_ids=task_ids, url_format=url_format)
