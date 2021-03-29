import json
import time
from typing import List, Dict
from urllib.parse import urlencode, unquote

from scrapy import Request, FormRequest, Selector

from crawler.core_terminal.base_spiders import BaseMultiTerminalSpider
from crawler.core_terminal.items import (
    BaseTerminalItem, DebugItem, TerminalItem, InvalidContainerNoItem
)
from crawler.core_terminal.rules import RuleManager, BaseRoutingRule, RequestOption


BASE_URL = 'https://csp.poha.com'


class TerminalBayportMultiSpider(BaseMultiTerminalSpider):
    name = 'terminal_bayport_multi'

    def __init__(self, *args, **kwargs):
        super(TerminalBayportMultiSpider, self).__init__(*args, **kwargs)

        rules = [
            LoginRoutingRule(),
            ContainerRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)

    def start(self):
        option = LoginRoutingRule.build_request_option(container_no_list=self.container_no_list)
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
            return Request(
                url=option.url,
                headers=option.headers,
                meta=meta,
                dont_filter=True,
            )
        elif option.method == RequestOption.METHOD_POST_FORM:
            return FormRequest(
                url=option.url,
                formdata=option.form_data,
                headers=option.headers,
                meta=meta,
                dont_filter=True,
            )
        elif option.method == RequestOption.METHOD_POST_BODY:
            return FormRequest(
                url=option.url,
                headers=option.headers,
                body=option.body,
                meta=meta,
                dont_filter=True,
            )
        else:
            raise ValueError(f'Invalid option.method [{option.method}]')


# -------------------------------------------------------------------------------


class LoginRoutingRule(BaseRoutingRule):
    name = 'Login'

    @classmethod
    def build_request_option(cls, container_no_list: List[str]) -> RequestOption:
        url = f'{BASE_URL}/Lynx/VITTerminalAccess/Login.aspx'
        form_data = {
            'User': 'hard202006010',
            'Pass': '*r@y39=9q-!k',
        }

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_POST_BODY,
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            url=url,
            body=urlencode(form_data),
            meta={'container_no_list': container_no_list},
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.html'

    def handle(self, response):
        container_no_list = response.meta['container_no_list']

        for container_no in container_no_list:
            yield ContainerRoutingRule.build_request_option(container_no=container_no)


# -------------------------------------------------------------------------------


class ContainerRoutingRule(BaseRoutingRule):
    name = 'CONTAINER'

    @classmethod
    def build_request_option(cls, container_no) -> RequestOption:
        url = (
            f'{BASE_URL}/Lynx/VITTerminalAccess/GetEquipmentInformation.aspx?'
            f'Action=GET&ContainerNum={container_no}&ShowAll=true&_={cls.thirteen_digits_timestamp()}'
        )

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=url,
            meta={
                'container_no': container_no,
            },
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.html'

    def handle(self, response):
        container_no = response.meta['container_no']

        if self._is_container_no_invalid(response=response):
            yield InvalidContainerNoItem(container_no=container_no)
            return

        container_data = self.extract_container_data(response=response)
        container_histories = self.extract_container_histories(response=response)  # may contain gate_out date

        yield TerminalItem(
            container_no=container_no,
            container_spec=container_data['spec'],
            carrier=container_data['line'],
            mbl_no=container_data['mbl_no'],
            weight=container_data['weight'],
        )

    @staticmethod
    def _is_container_no_invalid(response: Selector) -> bool:
        return not bool(response.css('data Container'))

    @staticmethod
    def extract_container_data(response: Selector) -> Dict:
        container_data = response.css('data Container')

        size = container_data.css('EquipmentSize::text').get()
        height = container_data.css('EquipmentHeight::text').get()
        ttype = container_data.css('EquipmentType::text').get()

        return {
            'mbl_no': container_data.css('BillOfLadingNumber::text').get(),
            'spec': f'{size}/{ttype}/{height}',
            'weight': container_data.css('GrossWeight::text').get(),
            'line': container_data.css('ShippingLineId::text').get(),
        }

    @staticmethod
    def extract_container_histories(response: Selector):
        data = response.css('data')
        container_history = data.css('containerhistory::text').get()
        container_history_json = json.loads(container_history)

        results = []
        histories = container_history_json['aaData']
        for history in histories:
            results.append({
                'Performent': history[1],
                'Performer': history[2],
                'Event': history[3],
                'Notes': unquote(history[4]),
            })

        return results

    @staticmethod
    def thirteen_digits_timestamp():
        return round(time.time() * 1000)

