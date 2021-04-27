import json

from scrapy import Request, FormRequest, Selector

from crawler.core_terminal.base_spiders import BaseMultiTerminalSpider
from crawler.core_terminal.items import (
    BaseTerminalItem, DebugItem, TerminalItem, InvalidContainerNoItem
)
from crawler.core_terminal.rules import RuleManager, BaseRoutingRule, RequestOption
from crawler.extractors.table_extractors import BaseTableLocator, HeaderMismatchError, TableExtractor

BASE_URL = 'http://propassva.portofvirginia.com'


class TerminalVirginiaMultiSpider(BaseMultiTerminalSpider):
    name = 'terminal_virginia_multi'

    def __init__(self, *args, **kwargs):
        super(TerminalVirginiaMultiSpider, self).__init__(*args, **kwargs)

        rules = [
            ContainerRoutingRule(),
            ContainerDetailRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)

    def start(self):
        for container_no in self.container_no_list:
            option = ContainerRoutingRule.build_request_option(container_no=container_no)
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
        else:
            raise ValueError(f'Invalid option.method [{option.method}]')


# -------------------------------------------------------------------------------


class ContainerRoutingRule(BaseRoutingRule):
    name = 'CONTAINER'

    @classmethod
    def build_request_option(cls, container_no) -> RequestOption:
        url = f'{BASE_URL}/api/containers?search={container_no}'

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=url,
            meta={
                'container_no': container_no,
            },
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.json'

    def handle(self, response):
        container_no = response.meta['container_no']

        response_json = json.loads(response.text)

        for container_bar in response_json:
            fac = container_bar['facility']
            gkey = container_bar['gkey']
            yield ContainerDetailRoutingRule.build_request_option(
                container_no=container_no, gkey=gkey, facility=fac)


# -------------------------------------------------------------------------------


class ContainerDetailRoutingRule(BaseRoutingRule):
    name = 'CONTAINER_DETAIL'

    @classmethod
    def build_request_option(cls, container_no: str, gkey: str, facility: str) -> RequestOption:
        url = f'{BASE_URL}/api/containers/{gkey}/{facility}'

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=url,
            meta={
                'container_no': container_no
            }
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.json'

    def handle(self, response):
        container_no = response.meta['container_no']
        # it conclude Container data

        yield TerminalItem(
            container_no=container_no
        )

