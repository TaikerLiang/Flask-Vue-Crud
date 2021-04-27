from urllib.parse import urlencode, unquote
from datetime import datetime
import json
import time
from typing import List, Dict

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
        unique_container_nos = list(self.cno_tid_map.keys())
        option = LoginRoutingRule.build_request_option(container_no_list=unique_container_nos)
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
        yield ContainerRoutingRule.build_request_option(container_no_list=container_no_list)


# -------------------------------------------------------------------------------


class ContainerRoutingRule(BaseRoutingRule):
    name = 'CONTAINER'

    @classmethod
    def build_request_option(cls, container_no_list: List) -> RequestOption:
        params = {
            'WhichReq': 'Container',
            'ContainerNum': ','.join(container_no_list),
            'BOLNum': '',
            'PTD': '',
            'ContainerNotification': False,
            '_': cls.thirteen_digits_timestamp(),
        }
        url = f"https://csp.poha.com/Lynx/VITTerminalAccess/GetReleaseInquiryList.aspx?{urlencode(params)}"

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=url,
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.html'

    def handle(self, response):
        resp = json.loads(response.body)

        for row in resp['aaData']:
            yield TerminalItem(
                container_no=row[2],
                holds=row[5],
                customs_release=row[6],
                last_free_day=self._get_last_free_day(),
            )

    def _get_last_free_day(self, port_lfd='5/2/2021', line_lfd='5/3/2021'):
        port_lfd_dt = datetime.strptime(port_lfd, '%m/%d/%Y')
        line_lfd_dt = datetime.strptime(line_lfd, '%m/%d/%Y')

        if port_lfd_dt < line_lfd_dt:
            return port_lfd
        else:
            return line_lfd or port_lfd

    @staticmethod
    def thirteen_digits_timestamp():
        return round(time.time() * 1000)
