import json

import scrapy

from crawler.core_terminal.base_spiders import BaseMultiTerminalSpider
from crawler.core_terminal.exceptions import TerminalResponseFormatError, TerminalInvalidContainerNoError
from crawler.core_terminal.items import BaseTerminalItem, TerminalItem, DebugItem, InvalidContainerNoItem
from crawler.core_terminal.request_helpers import RequestOption
from crawler.core_terminal.rules import RuleManager, BaseRoutingRule


BASE_URL = 'https://www.apmterminals.com'


class ShareSpider(BaseMultiTerminalSpider):
    terminal_id = ''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        rules = [
            ContainerRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)

    def start(self):
        uni_container_nos = list(self.cno_tid_map.keys())
        option = ContainerRoutingRule.build_request_option(container_nos=uni_container_nos, terminal_id=self.terminal_id)
        yield self._build_request_by(option=option)

    def parse(self, response):
        yield DebugItem(info={'meta': dict(response.meta)})

        routing_rule = self._rule_manager.get_rule_by_response(response=response)

        save_name = routing_rule.get_save_name(response=response)
        self._saver.save(to=save_name, text=response.text)

        for result in routing_rule.handle(response=response):
            if isinstance(result, TerminalItem) or isinstance(result, InvalidContainerNoItem):
                c_no = result['container_no']
                t_ids = self.cno_tid_map[c_no]
                for t_id in t_ids:
                    result['task_id'] = t_id
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
                method='POST',
                url=option.url,
                headers=option.headers,
                body=option.body,
                meta=meta,
            )

        else:
            raise KeyError()


class TerminalApmPESpider(ShareSpider):
    name = 'terminal_apm_pe_multi'
    terminal_id = 'cfc387ee-e47e-400a-80c5-85d4316f1af9'


class TerminalApmLASpider(ShareSpider):
    name = 'terminal_apm_la_multi'
    terminal_id = 'c56ab48b-586f-4fd2-9a1f-06721c94f3bb'


class ContainerRoutingRule(BaseRoutingRule):
    name = 'CONTAINER'

    @classmethod
    def build_request_option(cls, container_nos, terminal_id) -> RequestOption:
        url = f'{BASE_URL}/apm/api/trackandtrace/import-availability'

        form_data = {
            'DateFormat': 'dd/MM/yy',
            'Ids': container_nos,
            'TerminalId': terminal_id,
        }

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_POST_BODY,
            url=url,
            headers={'Content-Type': 'application/json'},
            body=json.dumps(form_data),
            meta={'container_nos': container_nos}
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.json'

    def handle(self, response):
        container_nos = response.meta['container_nos']

        response_json = json.loads(response.text)
        for container in response_json['ContainerAvailabilityResults']:
            result = {
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
                'holds': ','.join(container['Holds']),
                'cy_location': container['YardLocation'],
                'vessel': container['VesselName'],
                'mbl_no': container['BillOfLading'][0],
                'weight': container['GrossWeight'],
                'hazardous': container['HazardousClass'] or None,
            }

            container_nos.remove(container['ContainerId'])
            yield TerminalItem(**result)

        for container_no in container_nos:
            yield InvalidContainerNoItem(container_no=container_no)

    @staticmethod
    def _is_all_container_nos_invalid(response_json):
        container_results = response_json['ContainerAvailabilityResults']

        if not container_results:
            return True

        return False

    @staticmethod
    def __check_expected_container_format(container):
        if len(container['Holds']) >= 2:
            raise TerminalResponseFormatError(reason=f'Unexpected Holds: `{container["Holds"]}`')

        elif len(container['BillOfLading']) != 1:
            raise TerminalResponseFormatError(reason=f'Unexpected Mbl_no: `{container["BillOfLading"]}`')

