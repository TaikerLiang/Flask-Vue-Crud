import re

import scrapy

from crawler.core_terminal.base_spiders import BaseTerminalSpider
from crawler.core_terminal.exceptions import TerminalResponseFormatError, TerminalInvalidContainerNoError
from crawler.core_terminal.items import BaseTerminalItem, DebugItem, TerminalItem
from crawler.core_terminal.request_helpers import RequestOption
from crawler.core_terminal.rules import RuleManager, BaseRoutingRule


BASE_URL = 'https://pct.tideworks.com'
EMAIL = 'm10715033@mail.ntust.edu.tw'
PASSWORD = '1234567890'


class TerminalPctSpider(BaseTerminalSpider):
    name = 'terminal_pct'

    def __init__(self, *args, **kwargs):
        super(TerminalPctSpider, self).__init__(*args, **kwargs)

        rules = [
            LoginRoutingRule(),
            SearchContainerRoutingRule(),
            ContainerDetailRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)

    def start(self):
        option = LoginRoutingRule.build_request_option(container_no=self.container_no)
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

        if option.method == RequestOption.METHOD_POST_FORM:
            return scrapy.FormRequest(
                url=option.url,
                formdata=option.form_data,
                meta=meta,
            )

        elif option.method == RequestOption.METHOD_GET:
            return scrapy.Request(
                url=option.url,
                meta=meta,
            )

        else:
            raise RuntimeError()


# -------------------------------------------------------------------------------


class LoginRoutingRule(BaseRoutingRule):
    name = 'LOGIN'

    @classmethod
    def build_request_option(cls, container_no) -> RequestOption:
        url = f'{BASE_URL}/fc-PCT/j_spring_security_check'
        form_data = {
            'j_username': EMAIL,
            'j_password': PASSWORD,
        }

        return RequestOption(
            method=RequestOption.METHOD_POST_FORM,
            rule_name=cls.name,
            url=url,
            form_data=form_data,
            meta={'container_no': container_no},
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.html'

    def handle(self, response):
        container_no = response.meta['container_no']

        yield SearchContainerRoutingRule.build_request_option(container_no=container_no)


# -------------------------------------------------------------------------------


class SearchContainerRoutingRule(BaseRoutingRule):
    name = 'SEARCH_CONTAINER'

    @classmethod
    def build_request_option(cls, container_no) -> RequestOption:
        url = f'{BASE_URL}/fc-PCT/import/default.do?method=defaultSearch'
        form_data = {
            'searchBy': 'CTR',
            'numbers': container_no,
        }

        return RequestOption(
            method=RequestOption.METHOD_POST_FORM,
            rule_name=cls.name,
            url=url,
            form_data=form_data,
            meta={'container_no': container_no},
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.html'

    def handle(self, response):
        if self.__is_invalid_container_no(response=response):
            raise TerminalInvalidContainerNoError()

        # for ContainerDetailRoutingRule request
        container_url = self.__get_first_container_url(response=response)

        yield ContainerDetailRoutingRule.build_request_option(container_url=container_url)

    @staticmethod
    def __get_first_container_url(response: scrapy.Selector) -> str:
        url = response.css('div#result tr td a::attr(href)').get()
        return url

    @staticmethod
    def __is_invalid_container_no(response: scrapy.Selector) -> bool:
        message = response.css('div#result tr td a::text').get().strip()

        if message == 'Check nearby locations':
            return True
        else:
            return False


# -------------------------------------------------------------------------------


class ContainerDetailRoutingRule(BaseRoutingRule):
    name = 'CONTAINER_DETAIL'

    @classmethod
    def build_request_option(cls, container_url) -> RequestOption:
        url = f'{BASE_URL}{container_url}'

        return RequestOption(
            method=RequestOption.METHOD_GET,
            rule_name=cls.name,
            url=url,
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.html'

    def handle(self, response):
        container_no = self.__extract_container_no(response=response)
        container_info = self.__extract_container_info(response=response)
        extra_container_info = self.__extract_extra_container_info(response=response)

        yield TerminalItem(
            container_no=container_no,
            **container_info,
            **extra_container_info,
        )

    @staticmethod
    def __extract_container_no(response: scrapy.Selector):
        pattern = re.compile(r'^Container - (?P<container_no>.+)$')

        container_no_text = response.css('div.page-header h2::text').get()
        m = pattern.match(container_no_text)
        container_no = m.group('container_no')

        return container_no

    def __extract_container_info(self, response: scrapy.Selector):
        pattern = re.compile(r'^(?P<vessel>[\w\s]+)/')
        container_info = {}

        div_selector = response.css('div.col-sm-4 div')
        for div in div_selector:
            key, value = self.__extract_container_info_div_text(div)
            container_info[key] = value

        m = pattern.match(container_info['Vessel/Voyage'])
        vessel = m.group('vessel')
        return {
            'discharge_date': container_info['Unload Date'],
            'ready_for_pick_up': container_info['Available for pickup'],
            'container_spec': container_info['Size/Type'],
            'carrier': container_info['Line'],
            'cy_location': container_info['Location'],
            'vessel': vessel,
            'weight': self.__reformat_weight(container_info['Weight']),
        }

    def __extract_extra_container_info(self, response: scrapy.Selector):
        extra_container_info = {}

        div_selector = response.css('div.col-sm-6 div')
        for div in div_selector:
            key, value = self.__extract_extra_container_info_div_text(div)
            extra_container_info[key] = value

        div_selector = response.css('div.col-sm-2 div')[:2]
        for div in div_selector:
            key, value = self.__extract_extra_container_info_div_text(div)
            extra_container_info[key] = value

        return {
            'freight_release': extra_container_info['Line Release Status'],
            'customs_release': extra_container_info['Customs Release Status'],
            'last_free_day': extra_container_info['Satisfied Thru'],
            'demurrage': extra_container_info['Demurrage'],
            'holds': extra_container_info['Holds'],
        }

    @staticmethod
    def __reformat_weight(weight_text_list):
        return ' '.join(weight_text_list.split())

    @staticmethod
    def __extract_container_info_div_text(div: scrapy.Selector):
        div_text_list = div.css('::text').getall()

        if len(div_text_list) == 4:
            key = div_text_list[0].strip()
            key = key[:-1]  # delete colon
            value = div_text_list[3].strip()
            return key, value

        elif len(div_text_list) in [2, 3]:
            key = div_text_list[0].strip()
            key = key[:-1]  # delete colon
            value = div_text_list[1].strip()
            return key, value

        else:
            raise TerminalResponseFormatError(reason='container_no_div format error')

    @staticmethod
    def __extract_extra_container_info_div_text(div: scrapy.Selector):
        div_text_list = div.css('::text').getall()

        key = div_text_list[0].strip()
        key = key[:-1]  # delete colon
        value = ''.join(div_text_list[1:]).strip()
        return key, value
