import json

import scrapy

from crawler.core_terminal.base_spiders import BaseTerminalSpider
from crawler.core_terminal.exceptions import TerminalResponseFormatError, TerminalInvalidContainerNoError
from crawler.core_terminal.items import BaseTerminalItem, TerminalItem, DebugItem
from crawler.core_terminal.request_helpers import RequestOption
from crawler.core_terminal.rules import RuleManager, BaseRoutingRule


BASE_URL = 'https://www.apmterminals.com'


class ShareSpider(BaseTerminalSpider):
    terminal_id = ''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        rules = [
            ContainerRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)

    def start(self):
        option = ContainerRoutingRule.build_request_option(container_no=self.container_no, terminal_id=self.terminal_id)
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

        if option.method == RequestOption.METHOD_POST_BODY:
            return scrapy.Request(
                method='POST',
                url=option.url,
                headers=option.headers,
                body=option.body,
                meta=meta,
            )

        else:
            raise KeyError()


class TerminalApmPESpider(ShareSpider):
    name = 'terminal_apm_pe'
    terminal_id = 'cfc387ee-e47e-400a-80c5-85d4316f1af9'


class TerminalApmLASpider(ShareSpider):
    name = 'terminal_apm_la'
    terminal_id = 'c56ab48b-586f-4fd2-9a1f-06721c94f3bb'


class ContainerRoutingRule(BaseRoutingRule):
    name = 'CONTAINER'

    @classmethod
    def build_request_option(cls, container_no, terminal_id) -> RequestOption:
        url = f'{BASE_URL}/apm/api/trackandtrace/import-availability'

        form_data = {
            'DateFormat': 'dd/MM/yy',
            'Ids': [container_no],
            'TerminalId': terminal_id,
        }

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_POST_BODY,
            url=url,
            headers={'Content-Type': 'application/json'},
            body=json.dumps(form_data),
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.json'

    def handle(self, response):
        response_json = json.loads(response.text)
        if self.__is_container_no_invalid(response_json):
            raise TerminalInvalidContainerNoError()

        container_result = self.__extract_container_result(response_json=response_json)

        yield TerminalItem(**container_result)

    @staticmethod
    def __is_container_no_invalid(response_json):
        container_results = response_json['ContainerAvailabilityResults']

        if not container_results:
            return True

        return False

    def __extract_container_result(self, response_json):
        container_results = response_json['ContainerAvailabilityResults']
        container = container_results[0]  # only one container
        self.__check_expected_container_format(container)

        return {
            'container_no': container['ContainerId'],
            'freight_release': container['Freight'],
            'customs_release': container['Customs'],
            'discharge_date': container['DischargedDate'] or None,
            'ready_for_pick_up': container['ReadyForDelivery'],
            'appointment_date': container['AppointmentDate'],
            'last_free_day': container['StoragePaidThroughDate'] or None,
            'gate_out_date': container['GateOutDate'] or None,
            'demurrage': container['Demurrage'] or None,
            'carrier': container['LineId'],
            'container_spec': container['SizeTypeHeight'],
            'holds': container['Holds'][0] if container['Holds'] else None,
            'cy_location': container['YardLocation'],
            'vessel': container['VesselName'],
            'mbl_no': container['BillOfLading'][0],
            'weight': container['GrossWeight'],
            'hazardous': container['HazardousClass'] or None,
        }

    @staticmethod
    def __check_expected_container_format(container):
        if len(container['Holds']) >= 2:
            raise TerminalResponseFormatError(reason=f'Unexpected Holds: `{container["Holds"]}`')

        elif len(container['BillOfLading']) != 1:
            raise TerminalResponseFormatError(reason=f'Unexpected Mbl_no: `{container["BillOfLading"]}`')

