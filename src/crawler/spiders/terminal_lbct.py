import json
import time
from typing import Dict, List

import scrapy

from crawler.core_terminal.base_spiders import BaseMultiTerminalSpider
from crawler.core_terminal.items import DebugItem, TerminalItem, InvalidContainerNoItem
from crawler.core_terminal.request_helpers import RequestOption
from crawler.core_terminal.rules import RuleManager, BaseRoutingRule


BASE_URL = "https://www.lbct.com"
MAX_PAGE_NUM = 20


class TerminalLbctSpider(BaseMultiTerminalSpider):
    firms_code = "WAC8"
    name = "terminal_lbct"

    def __init__(self, *args, **kwargs):
        super(TerminalLbctSpider, self).__init__(*args, **kwargs)

        rules = [
            ContainerRoutingRule(),
            NextRoundRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)

    def start(self):
        unique_container_nos = list(self.cno_tid_map.keys())
        option = ContainerRoutingRule.build_request_option(container_no_list=unique_container_nos)
        yield self._build_request_by(option=option)

    def parse(self, response):
        yield DebugItem(info={"meta": dict(response.meta)})

        routing_rule = self._rule_manager.get_rule_by_response(response=response)

        save_name = routing_rule.get_save_name(response=response)
        self._saver.save(to=save_name, text=response.text)

        for result in routing_rule.handle(response=response):
            if isinstance(result, TerminalItem) or isinstance(result, InvalidContainerNoItem):
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

        if option.method == RequestOption.METHOD_GET:
            return scrapy.Request(
                url=option.url,
                meta=meta,
                dont_filter=True,
            )

        else:
            raise RuntimeError()


# -------------------------------------------------------------------------------


class ContainerRoutingRule(BaseRoutingRule):
    name = "CONTAINER"

    @classmethod
    def build_request_option(cls, container_no_list: List) -> RequestOption:
        timestamp = cls._build_timestamp()
        url = f'{BASE_URL}/CargoSearch/GetMultiCargoSearchJson?timestamp={timestamp}&listOfSearchId={",".join(container_no_list[:MAX_PAGE_NUM])}'

        return RequestOption(
            rule_name=cls.name, method=RequestOption.METHOD_GET, url=url, meta={"container_no_list": container_no_list}
        )

    def get_save_name(self, response) -> str:
        return f"{self.name}.json"

    def handle(self, response):
        container_no_list = response.meta["container_no_list"]
        response_dict = json.loads(response.text)

        for response in response_dict:
            if not response["containerId"] in container_no_list:
                continue

            container_info = self._extract_container_info(response=response)

            yield TerminalItem(
                container_no=container_info["container_no"],
                carrier_release=container_info["freight_hold"],
                customs_release=container_info["customs_hold"],
                discharge_date=container_info["discharge_date"],
                ready_for_pick_up=container_info["ready_for_pick_up"],
                appointment_date=container_info["appointment_date"],
                gate_out_date=container_info["gate_out_date"],
                last_free_day=container_info["last_free_day"],
                carrier=container_info["carrier"],
                container_spec=container_info["type"],
                cy_location=container_info["location"],
                vessel=container_info["vessel"],
                voyage=container_info["voyage"],
                # on html
                # field same like other terminal
                tmf=container_info["tmf_hold"],
                # new field
                owed=container_info["owed"],
                full_empty=container_info["full/empty"],
            )

        yield NextRoundRoutingRule.build_request_option(container_no_list=container_no_list)

    @staticmethod
    def _extract_container_info(response: Dict) -> Dict:
        # pattern = re.compile(r'^(?P<discharge_date>\d{2}/\d{2}/\d{4})')
        appt_date_time = None
        if response.get("fakeId"):
            raw_appt_date_time = response["fakeId"]
            appt_date_time = raw_appt_date_time.split("#")[0]

        tmf, customs, freight = None, None, None
        if response.get("listOfFlag"):
            for flag in response["listOfFlag"]:
                if flag["holdName"] == "TMF_CONTAINER_HOLD":
                    tmf = flag["type"]
                elif flag["holdName"] == "CUSTOMS_DEFAULT_HOLD":
                    customs = flag["type"]
                elif flag["holdName"] == "FREIGHT_BL_HOLD":
                    freight = flag["type"]

        # m = pattern.match(container['discharged'])
        # discharge_date = m.group('discharge_date')

        return {
            "container_no": response["containerId"],
            "discharge_date": response["discharged"],
            "type": response["type"],
            "ready_for_pick_up": response["available"],
            "last_free_day": response["freeTimeExpiration"],
            "appointment_date": appt_date_time,
            "gate_out_date": response["dateDeliverd"],
            "vessel": response["vessel"],
            "voyage": response["inboundVoyageNumber"],
            "carrier": response["line"],
            "location": response["location"],
            "full/empty": response["freightKind"],
            "tmf_hold": tmf,
            "customs_hold": customs,
            "freight_hold": freight,
            "owed": response["owed"],
        }

    @staticmethod
    def _build_timestamp():
        return int(time.time() * 1000)


class NextRoundRoutingRule(BaseRoutingRule):
    name = "NEXT_ROUND"

    @classmethod
    def build_request_option(cls, container_no_list: List) -> RequestOption:
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url="https://www.google.com",
            meta={
                "container_no_list": container_no_list,
            },
        )

    def handle(self, response):
        container_no_list = response.meta["container_no_list"]

        if len(container_no_list) <= MAX_PAGE_NUM:
            return

        container_no_list = container_no_list[MAX_PAGE_NUM:]

        yield ContainerRoutingRule.build_request_option(container_no_list=container_no_list)
