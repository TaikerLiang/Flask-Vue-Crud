import json
import re
import time
from typing import Dict

import scrapy

from crawler.core_terminal.base_spiders import BaseTerminalSpider
from crawler.core_terminal.items import DebugItem, BaseTerminalItem, TerminalItem
from crawler.core_terminal.request_helpers import RequestOption
from crawler.core_terminal.rules import RuleManager, BaseRoutingRule


BASE_URL = 'https://www.lbct.com'


class TerminalLbctSpider(BaseTerminalSpider):
    name = 'terminal_lbct'

    def __init__(self, *args, **kwargs):
        super(TerminalLbctSpider, self).__init__(*args, **kwargs)

        rules = [
            ContainerRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)

    def start(self):
        option = ContainerRoutingRule.build_request_option(container_no=self.container_no)
        yield self._build_request_by(option=option)

    def parse(self, response):
        yield DebugItem(info={'meta': dict(response.meta)})

        routing_rule = self._rule_manager.get_rule_by_response(response=response)

        save_name = routing_rule.get_save_name(response=response)
        self._saver.save(to=save_name, text=response.text)

        for result in routing_rule.handle(response=response):
            if isinstance(result, BaseTerminalItem):
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
            )

        else:
            raise RuntimeError()


# -------------------------------------------------------------------------------


class ContainerRoutingRule(BaseRoutingRule):
    name = 'CONTAINER'

    @classmethod
    def build_request_option(cls, container_no) -> RequestOption:
        timestamp = cls._build_timestamp()
        url = f'{BASE_URL}/CargoSearch/GetMultiCargoSearchJson?timestamp={timestamp}&listOfSearchId={container_no}'

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=url,
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.json'

    def handle(self, response):
        response_dict = json.loads(response.text)

        container_info = self._extract_container_info(response_dict=response_dict)

        yield TerminalItem(
            container_no=container_info['container_no'],
            freight_release=container_info['freight_hold'],
            customs_release=container_info['customs_hold'],
            discharge_date=container_info['discharge_date'],
            ready_for_pick_up=container_info['ready_for_pick_up'],
            appointment_date=container_info['appointment_date'],
            last_free_day=container_info['last_free_day'],
            carrier=container_info['carrier'],
            container_spec=container_info['type'],
            cy_location=container_info['location'],
            vessel=container_info['vessel'],
            voyage=container_info['voyage'],

            # on html
            # field same like other terminal
            tmf=container_info['tmf_hold'],

            # new field
            owed=container_info['owed'],
            full_empty=container_info['full/empty'],
        )

    @staticmethod
    def _extract_container_info(response_dict: Dict) -> Dict:
        # pattern = re.compile(r'^(?P<discharge_date>\d{2}/\d{2}/\d{4})')

        first_container = response_dict[0]

        appt_date_time = None
        if first_container.get('fakeId'):
            raw_appt_date_time = first_container['fakeId']
            appt_date_time = raw_appt_date_time.split('#')[0]

        tmf, customs, freight = None, None, None
        if first_container.get('listOfFlag'):
            tmf = first_container['listOfFlag'][0]['type']
            customs = first_container['listOfFlag'][1]['type']
            freight = first_container['listOfFlag'][2]['type']

        # m = pattern.match(container['discharged'])
        # discharge_date = m.group('discharge_date')

        return {
            'container_no': first_container['containerId'],
            'discharge_date': first_container['discharged'],
            'type': first_container['type'],
            'ready_for_pick_up': first_container['available'],
            'last_free_day': first_container['freeTimeExpiration'],
            'appointment_date': appt_date_time,
            'vessel': first_container['vessel'],
            'voyage': first_container['inboundVoyageNumber'],
            'carrier': first_container['line'],
            'location': first_container['location'],
            'full/empty': first_container['freightKind'],
            'tmf_hold': tmf,
            'customs_hold': customs,
            'freight_hold': freight,
            'owed': first_container['owed'],
        }

    @staticmethod
    def _build_timestamp():
        return int(time.time() * 1000)


