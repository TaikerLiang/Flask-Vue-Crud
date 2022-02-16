import json
from typing import List

import scrapy

from crawler.core.proxy import HydraproxyProxyManager
from crawler.core_terminal.base import TERMINAL_RESULT_STATUS_ERROR
from crawler.core_terminal.base_spiders import BaseMultiTerminalSpider
from crawler.core_terminal.exceptions import TerminalResponseFormatError
from crawler.core_terminal.items import (
    BaseTerminalItem,
    DebugItem,
    ExportErrorData,
    TerminalItem,
)
from crawler.core_terminal.request_helpers import RequestOption
from crawler.core_terminal.rules import BaseRoutingRule, RuleManager

BASE_URL = "https://www.apmterminals.com"


class ApmShareSpider(BaseMultiTerminalSpider):
    terminal_id = ""
    data_source_id = ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        rules = [
            ContainerRoutingRule(),
            NextRoundRoutingRule(),
        ]
        self._proxy_manager = HydraproxyProxyManager(session="share", logger=self.logger)
        self._rule_manager = RuleManager(rules=rules)

    def start(self):
        unique_container_nos = list(self.cno_tid_map.keys())
        option = self._prepare_start(unique_container_nos=unique_container_nos)
        yield self._build_request_by(option=option)

    def _prepare_start(self, unique_container_nos: List):
        self._proxy_manager.renew_proxy()
        option = ContainerRoutingRule.build_request_option(
            container_nos=unique_container_nos,
            terminal_id=self.terminal_id,
            data_source_id=self.data_source_id,
        )
        proxy_option = self._proxy_manager.apply_proxy_to_request_option(option=option)
        return proxy_option

    def parse(self, response):
        yield DebugItem(info={"meta": dict(response.meta)})

        routing_rule = self._rule_manager.get_rule_by_response(response=response)

        save_name = routing_rule.get_save_name(response=response)
        self._saver.save(to=save_name, text=response.text)

        for result in routing_rule.handle(response=response):
            if isinstance(result, TerminalItem) or isinstance(result, ExportErrorData):
                c_no = result["container_no"]
                t_ids = self.cno_tid_map[c_no]
                for t_id in t_ids:
                    result["task_id"] = t_id
                    yield result
            elif isinstance(result, BaseTerminalItem):
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

        if option.method == RequestOption.METHOD_POST_BODY:
            return scrapy.Request(
                method="POST",
                url=option.url,
                headers=option.headers,
                body=option.body,
                meta=meta,
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
            raise KeyError()


class ContainerRoutingRule(BaseRoutingRule):
    name = "CONTAINER"

    @classmethod
    def build_request_option(cls, container_nos, terminal_id, data_source_id) -> RequestOption:
        url = f"{BASE_URL}/apm/api/trackandtrace/import-availability"

        form_data = {
            "DateFormat": "dd/MM/yy",
            "Ids": container_nos[:20],  # page size == 20
            "TerminalId": terminal_id,
            "DatasourceId": data_source_id,
        }

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_POST_BODY,
            url=url,
            headers={"Content-Type": "application/json"},
            body=json.dumps(form_data),
            meta={
                "container_nos": container_nos,
                "terminal_id": terminal_id,
                "data_source_id": data_source_id,
            },
        )

    def get_save_name(self, response) -> str:
        return f"{self.name}.json"

    def handle(self, response):
        container_nos = response.meta["container_nos"]
        terminal_id = response.meta["terminal_id"]
        data_source_id = response.meta["data_source_id"]

        cur_container_nos = container_nos[:20]
        response_json = json.loads(response.text)
        for container in response_json["ContainerAvailabilityResults"]:
            result = {
                "container_no": container["ContainerId"],
                "carrier_release": container["Freight"],
                "customs_release": container["Customs"],
                "discharge_date": container["DischargedDate"] or None,
                "ready_for_pick_up": container["ReadyForDelivery"],
                "appointment_date": container["AppointmentDate"],
                "last_free_day": container["StoragePaidThroughDate"] or None,
                "gate_out_date": container["GateOutDate"] or None,
                "demurrage": container["Demurrage"] or None,
                "carrier": container["LineId"],
                "container_spec": container["SizeTypeHeight"],
                "holds": ",".join(container["Holds"]),
                "cy_location": container["YardLocation"],
                "vessel": container["VesselName"],
                "mbl_no": container["BillOfLading"][0] if container["BillOfLading"] else None,
                "weight": container["GrossWeight"],
                "hazardous": container["HazardousClass"].strip() or None,
            }

            cur_container_nos.remove(container["ContainerId"])
            yield TerminalItem(**result)

        for container_no in cur_container_nos:
            yield ExportErrorData(
                container_no=container_no,
                detail="Data was not found",
                status=TERMINAL_RESULT_STATUS_ERROR,
            )

        yield NextRoundRoutingRule.build_request_option(
            container_nos=container_nos, terminal_id=terminal_id, data_source_id=data_source_id
        )

    @staticmethod
    def _is_all_container_nos_invalid(response_json):
        container_results = response_json["ContainerAvailabilityResults"]

        if not container_results:
            return True

        return False

    @staticmethod
    def __check_expected_container_format(container):
        if len(container["Holds"]) >= 2:
            raise TerminalResponseFormatError(reason=f'Unexpected Holds: `{container["Holds"]}`')

        elif len(container["BillOfLading"]) != 1:
            raise TerminalResponseFormatError(reason=f'Unexpected Mbl_no: `{container["BillOfLading"]}`')


class NextRoundRoutingRule(BaseRoutingRule):
    @classmethod
    def build_request_option(cls, container_nos: List, terminal_id: str, data_source_id: str) -> RequestOption:
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url="https://eval.edi.hardcoretech.co/c/livez",
            meta={
                "container_nos": container_nos,
                "terminal_id": terminal_id,
                "data_source_id": data_source_id,
            },
        )

    def handle(self, response):
        container_nos = response.meta["container_nos"]
        terminal_id = response.meta["terminal_id"]
        data_source_id = response.meta["data_source_id"]

        if len(container_nos) <= 20:  # page size == 20
            return

        container_nos = container_nos[20:]

        yield ContainerRoutingRule.build_request_option(
            container_nos=container_nos, terminal_id=terminal_id, data_source_id=data_source_id
        )
