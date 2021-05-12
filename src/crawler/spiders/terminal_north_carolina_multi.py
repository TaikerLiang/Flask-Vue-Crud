import json
import time

from scrapy import Request, FormRequest, Selector

from crawler.core_terminal.base_spiders import BaseMultiTerminalSpider
from crawler.core_terminal.exceptions import LoginNotSuccessFatal
from crawler.core_terminal.items import BaseTerminalItem, DebugItem, TerminalItem, InvalidContainerNoItem
from crawler.core_terminal.rules import RuleManager, BaseRoutingRule, RequestOption
from crawler.extractors.table_extractors import BaseTableLocator, HeaderMismatchError, TableExtractor

BASE_URL = 'https://ecargo.ncports.com'


class TerminalNorthCarolinaMultiSpider(BaseMultiTerminalSpider):
    name = 'terminal_north_carolina_multi'

    def __init__(self, *args, **kwargs):
        super(TerminalNorthCarolinaMultiSpider, self).__init__(*args, **kwargs)

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
        else:
            raise ValueError(f'Invalid option.method [{option.method}]')


# -------------------------------------------------------------------------------


class LoginRoutingRule(BaseRoutingRule):
    name = 'LOGIN'

    @classmethod
    def build_request_option(cls, container_no_list) -> RequestOption:
        url = f'{BASE_URL}/j_spring_security_check'
        form_data = {
            'j_username': 'SLU13',
            'j_password': 'HARDC0RE',
            'tmnl_cd': 'WIL',
            'ydTmnlName': 'NCSPA',
            'noOfLoginAttempts': '1',
        }

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_POST_FORM,
            url=url,
            form_data=form_data,
            meta={
                'container_no_list': container_no_list,
            },
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.json'

    def handle(self, response):
        container_no_list = response.meta['container_no_list']

        response_json = json.loads(response.text)
        if response_json['success'] is not True:
            raise LoginNotSuccessFatal(success_status=response_json['success'])

        yield ContainerRoutingRule.build_request_option(container_no_list=container_no_list)


# -------------------------------------------------------------------------------


class ContainerRoutingRule(BaseRoutingRule):
    name = 'CONTAINER'

    @classmethod
    def build_request_option(cls, container_no_list) -> RequestOption:
        _dc = round(time.time() * 1000)
        ctrNo = '%0A'.join(container_no_list)
        url = f'{BASE_URL}/containerreport/getctrlist?_dc={_dc}&ctrNo={ctrNo}&page=1&start=0&limit=100'

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=url,
            meta={
                'container_no_list': container_no_list,
            },
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.json'

    def handle(self, response):
        container_no_list = response.meta['container_no_list']

        response_json = json.loads(response.text)
        datas = response_json['data']

        for data in datas:
            yield TerminalItem(
                container_no=data['ctrNo'],
                carrier=data['lineCd'],
                container_spec=f"{data['ctrSize']}/{data['ctrType']}/{data['ctrHt']}",
                vessel=data['vslNm'],
                weight=data['ctrWt'],
                holds=data['holdFlg'],
            )

        # there are another query: container history
