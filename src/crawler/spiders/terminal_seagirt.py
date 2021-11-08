import json
from typing import List

from scrapy import Request

from crawler.core_terminal.base_spiders import BaseMultiTerminalSpider
from crawler.core_terminal.items import DebugItem, TerminalItem, InvalidContainerNoItem
from crawler.core_terminal.rules import RuleManager, BaseRoutingRule, RequestOption

BASE_URL = 'https://twpapi.pachesapeake.com'


class TerminalSeagirtSpider(BaseMultiTerminalSpider):
    firms_code = 'C324'
    name = 'terminal_seagirt'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        rules = [
            ContainerRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)

    def start(self):
        unique_container_nos = list(self.cno_tid_map.keys())
        option = ContainerRoutingRule.build_request_option(container_nos=unique_container_nos)
        yield self._build_request_by(option=option)

    def parse(self, response):
        yield DebugItem(info={'meta': dict(response.meta)})

        routing_rule = self._rule_manager.get_rule_by_response(response=response)

        save_name = routing_rule.get_save_name(response=response)
        self._saver.save(to=save_name, text=response.text)

        for result in routing_rule.handle(response=response):
            if isinstance(result, TerminalItem) or isinstance(result, InvalidContainerNoItem):
                c_no = result['container_no']
                if c_no:
                    t_ids = self.cno_tid_map[c_no]
                    for t_id in t_ids:
                        result['task_id'] = t_id
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
            return Request(
                url=option.url,
                headers=option.headers,
                meta=meta,
                dont_filter=True,
            )
        else:
            raise ValueError(f'Invalid option.method [{option.method}]')


# -------------------------------------------------------------------------------


class ContainerRoutingRule(BaseRoutingRule):
    name = 'CONTAINER'

    @classmethod
    def build_request_option(cls, container_nos: List) -> RequestOption:
        container_no_str = '%2C'.join(container_nos)
        url = f"{BASE_URL}/api/track/GetContainers?siteId=SGT_BAL&key={container_no_str}"

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=url,
            headers={"Accept": "application/json"},
            meta={
                'container_nos': container_nos,
            },
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.json'

    def handle(self, response):
        response_dict = json.loads(response.text)
        container_nos = response.meta['container_nos']

        for container in response_dict:
            height = container["Height"].replace("\"", "")
            container_no = container["ContainerNumber"]
            yield TerminalItem(
                container_no=container_no,
                ready_for_pick_up=container["AvailabilityDisplayStatus"],
                customs_release=container["CustomReleaseStatus"],
                carrier_release=container["CarrierReleaseStatus"],
                last_free_day=container["LastFreeDt"],
                container_spec=f'{container["Length"]}/{container["Type"]}/{height}',
                demurrage=container["DemurrageAmount"],
                carrier=container["CarrierName"],
                holds=container["CarrierHold"],
                vessel=container["VesselCode"],
                voyage=container["VoyageNumber"],
                mbl_no=container["BillOfLadingNumber"],
                weight=container["GrossWeight"],
                discharge_date=container["DischargeTime"],
                demurrage_status=container["DemurrageStatus"],
            )
            container_nos.remove(container_no)

        for container_no in container_nos:
            yield InvalidContainerNoItem(container_no=container_no)
