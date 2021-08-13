import dataclasses
import re

import scrapy

from crawler.core_terminal.base_spiders import BaseMultiTerminalSpider
from crawler.core_terminal.exceptions import TerminalResponseFormatError
from crawler.core_terminal.items import DebugItem, TerminalItem, InvalidContainerNoItem
from crawler.core_terminal.request_helpers import RequestOption
from crawler.core_terminal.rules import RuleManager, BaseRoutingRule


@dataclasses.dataclass
class CompanyInfo:
    lower_short: str
    upper_short: str
    email: str
    password: str


class TideworksShareSpider(BaseMultiTerminalSpider):
    name = ''
    company_info = CompanyInfo(
        lower_short='',
        upper_short='',
        email='',
        password='',
    )

    def __init__(self, *args, **kwargs):
        super(TideworksShareSpider, self).__init__(*args, **kwargs)

        rules = [
            LoginRoutingRule(),
            SearchContainerRoutingRule(),
            ContainerDetailRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)

    def start(self):
        unique_container_nos = list(self.cno_tid_map.keys())
        option = LoginRoutingRule.build_request_option(
            container_nos=unique_container_nos, company_info=self.company_info
        )
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
    def build_request_option(cls, container_nos, company_info: CompanyInfo) -> RequestOption:
        url = f'https://{company_info.lower_short}.tideworks.com/fc-{company_info.upper_short}/j_spring_security_check'
        form_data = {
            'j_username': company_info.email,
            'j_password': company_info.password,
        }

        return RequestOption(
            method=RequestOption.METHOD_POST_FORM,
            rule_name=cls.name,
            url=url,
            form_data=form_data,
            meta={'container_nos': container_nos, 'company_info': company_info},
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.html'

    def handle(self, response):
        container_nos = response.meta['container_nos']
        company_info = response.meta['company_info']
        for container_no in container_nos:
            yield SearchContainerRoutingRule.build_request_option(container_no=container_no, company_info=company_info)


# -------------------------------------------------------------------------------


class SearchContainerRoutingRule(BaseRoutingRule):
    name = 'SEARCH_CONTAINER'

    @classmethod
    def build_request_option(cls, container_no, company_info: CompanyInfo) -> RequestOption:
        url = (
            f'https://{company_info.lower_short}.tideworks.com/fc-{company_info.upper_short}/'
            f'import/default.do?method=defaultSearch'
        )
        form_data = {
            'searchBy': 'CTR',
            'numbers': container_no,
        }

        return RequestOption(
            method=RequestOption.METHOD_POST_FORM,
            rule_name=cls.name,
            url=url,
            form_data=form_data,
            meta={'container_no': container_no, 'company_info': company_info},
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.html'

    def handle(self, response):
        container_no = response.meta['container_no']
        company_info = response.meta['company_info']

        if self._is_invalid_container_no(response=response):
            yield InvalidContainerNoItem(container_no=container_no)
            return

        # for ContainerDetailRoutingRule request
        container_url = self._get_first_container_url(response=response)

        yield ContainerDetailRoutingRule.build_request_option(container_url=container_url, company_info=company_info)

    @staticmethod
    def _get_first_container_url(response: scrapy.Selector) -> str:
        url = response.css('div#result tr td a::attr(href)').get()
        return url

    @staticmethod
    def _is_invalid_container_no(response: scrapy.Selector) -> bool:
        a_in_td = response.css('div#result tr td a')
        raw_all_text_in_td = response.css('div#result tr td ::text').getall()
        all_text_in_td = [text.strip() for text in raw_all_text_in_td]

        if not a_in_td or ('Check nearby locations' in all_text_in_td):
            return True
        else:
            return False


# -------------------------------------------------------------------------------


class ContainerDetailRoutingRule(BaseRoutingRule):
    name = 'CONTAINER_DETAIL'

    @classmethod
    def build_request_option(cls, container_url, company_info: CompanyInfo) -> RequestOption:
        url = f'https://{company_info.lower_short}.tideworks.com{container_url}'

        return RequestOption(
            method=RequestOption.METHOD_GET,
            rule_name=cls.name,
            url=url,
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.html'

    def handle(self, response):
        container_no = self._extract_container_no(response=response)
        container_info = self._extract_container_info(response=response)
        extra_container_info = self._extract_extra_container_info(response=response)

        yield TerminalItem(
            container_no=container_no,
            **container_info,
            **extra_container_info,
        )

    @staticmethod
    def _extract_container_no(response: scrapy.Selector):
        pattern = re.compile(r'^Container - (?P<container_no>.+)$')

        container_no_text = response.css('div.page-header h2::text').get()
        m = pattern.match(container_no_text)
        container_no = m.group('container_no')

        return container_no

    def _extract_container_info(self, response: scrapy.Selector):
        pattern = re.compile(r'^(?P<vessel>[\w\s]+)/')
        container_info = {}

        div_selectors = response.css('div.col-sm-4 div')
        for div in div_selectors:
            key, value = self._extract_container_info_div_text(div)
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
            'weight': self._reformat_weight(container_info['Weight']),
        }

    def _extract_extra_container_info(self, response: scrapy.Selector):
        extra_container_info = {}

        div_selector = response.css('div.col-sm-6 div')
        for div in div_selector:
            key, value = self._extract_extra_container_info_div_text_colsm6(div)
            if key:
                extra_container_info[key] = value

        div_selector = response.css('div.col-sm-2 div')[:2]
        for div in div_selector:
            key, value = self._extract_extra_container_info_div_text_colsm2(div)
            if key:
                extra_container_info[key] = value

        hold = extra_container_info['Holds']
        hold = None if hold == 'None' else hold

        return {
            'carrier_release': extra_container_info.get('Line Release Status', ''),
            'customs_release': extra_container_info.get('Customs Release Status', ''),
            'last_free_day': extra_container_info.get('Satisfied Thru', ''),
            'demurrage': extra_container_info.get('Demurrage', ''),
            'holds': hold,
        }

    @staticmethod
    def _reformat_weight(weight_text_list):
        return ' '.join(weight_text_list.split())

    @staticmethod
    def _extract_container_info_div_text(div: scrapy.Selector):
        div_text_list = div.css('::text').getall()

        if len(div_text_list) == 4:
            key = div_text_list[0].strip()
            key = key[:-1]  # delete colon
            value = div_text_list[3].strip()

        elif len(div_text_list) in [2, 3]:
            key = div_text_list[0].strip()
            key = key[:-1]  # delete colon
            value = div_text_list[1].strip()

        elif len(div_text_list) == 1:  # only title
            key = div_text_list[0].strip()
            key = key[:-1]  # delete colon
            value = None

        elif len(div_text_list) >= 6:
            key = div_text_list[0].strip()
            key = key[:-1]  # delete colon
            value = ' '.join([text.strip() for text in div_text_list[1:]])

        else:
            raise TerminalResponseFormatError(reason=f'unknown container_no_div format: `{div_text_list}`')

        return key, value

    @staticmethod
    def _extract_extra_container_info_div_text_colsm6(div: scrapy.Selector):
        div_text_list = div.css('::text').getall()
        div_text_list = [r.strip() for r in div_text_list if r.strip()]

        if len(div_text_list) >= 2:
            return div_text_list[0].replace(':', ''), div_text_list[1]
        elif len(div_text_list) == 1:
            tmp = div_text_list[0].split(':')
            tmp = [r.strip() for r in tmp if r.strip()]
            return tmp[0], tmp[1]
        return None, None

    @staticmethod
    def _extract_extra_container_info_div_text_colsm2(div: scrapy.Selector):
        div_text_list = div.css('::text').getall()

        key = div_text_list[0].strip()
        key = key[:-1]  # delete colon
        value = ''.join(div_text_list[1:]).strip()
        return key, value
