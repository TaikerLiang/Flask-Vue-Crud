import re
from typing import Dict

import scrapy

from crawler.core_terminal.base_spiders import BaseTerminalSpider
from crawler.core_terminal.exceptions import TerminalInvalidContainerNoError, TerminalInvalidMblNoError, \
    TerminalResponseFormatError
from crawler.core_terminal.items import BaseTerminalItem, DebugItem, TerminalItem
from crawler.core_terminal.request_helpers import RequestOption
from crawler.core_terminal.rules import RuleManager, BaseRoutingRule
from crawler.extractors.selector_finder import BaseMatchRule, find_selector_from

BASE_URL = 'https://www.ttilgb.com'
USER_ID = 'RLTC'
PASSWORD = 'Hardc0re'


class TerminalTTiSpider(BaseTerminalSpider):
    name = 'terminal_tti'

    def __init__(self, *args, **kwargs):
        super(TerminalTTiSpider, self).__init__(*args, **kwargs)

        rules = [
            LoginRoutingRule(),
            SearchContainerRoutingRule(),
            SearchMblRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)

    def start(self):
        option = LoginRoutingRule.build_request_option(container_no=self.container_no, mbl_no=self.mbl_no)
        yield self._build_request_by(option=option)

    def parse(self, response, **kwargs):
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
    def build_request_option(cls, container_no, mbl_no) -> RequestOption:
        url = f'{BASE_URL}/appAuthAction/login.do'
        form_data = {
            'pTmlCd': 'USLGB',
            'pUsrId': USER_ID,
            'pUsrPwd': PASSWORD,
        }

        return RequestOption(
            method=RequestOption.METHOD_POST_FORM,
            rule_name=cls.name,
            url=url,
            form_data=form_data,
            meta={'container_no': container_no, 'mbl_no': mbl_no},
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.html'

    def handle(self, response):
        container_no = response.meta['container_no']
        mbl_no = response.meta['mbl_no']

        yield SearchContainerRoutingRule.build_request_option(container_no=container_no)

        if mbl_no:
            yield SearchMblRoutingRule.build_request_option(mbl_no=mbl_no)


# -------------------------------------------------------------------------------


class SearchContainerRoutingRule(BaseRoutingRule):
    name = 'SEARCH_CONTAINER'

    @classmethod
    def build_request_option(cls, container_no) -> RequestOption:
        url = (
            f'{BASE_URL}/uiArp02Action/searchContainerInformationListByCntrNo.do?tmlCd=USLGB&srchTpCd=C&'
            f'cntrNo={container_no}&acssHis=USLGB,{USER_ID}'
        )

        return RequestOption(
            method=RequestOption.METHOD_GET,
            rule_name=cls.name,
            url=url,
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.html'

    def handle(self, response):
        scripts = response.css('script')
        result_match_rule = CssQueryResultExistMatchRule('::text')
        result_script = find_selector_from(scripts, rule=result_match_rule)

        result_script_text = result_script.css('::text').get()
        result_text = self._extract_result_text(text=result_script_text)
        if not result_text:
            raise TerminalInvalidContainerNoError()

        result = self._transform_results_text_to_dict(result_text=result_text)

        yield TerminalItem(
            container_no=result['cntrNo'],
            carrier=result['scacCd'],
            ready_for_pick_up=result.get('avlbFlg'),
            customs_release=result['custHold'],
            freight_release=result['cusmHold'],
            appointment_date=result['exstApntDt'],
            last_free_day=result.get('lstFreeDt'),
            container_spec=result['tmlPrivCntrTpszCdNm'],
            cy_location=result['lctnNm'],

            demurrage_due=result.get('dmgDueFlg'),
            pay_through_date=result.get('paidDt'),
            tmf=result.get('tmfFlg'),
        )

    @staticmethod
    def _extract_result_text(text: str):
        pattern = re.compile(r'\s+var\s+result\s+=\s+\[\{?(?P<results_text>.*)\}?\].+')
        match = pattern.match(text)
        results_text = match.group('results_text')
        results_text = results_text.replace('"', '')

        return results_text

    @staticmethod
    def _transform_results_text_to_dict(result_text: str) -> Dict:
        """
        result_text form: 'key1:value1,key2:value2,...,keyN:valueN'
        """
        result = {}

        result_tuples = result_text.split(',')
        for result_t in result_tuples:
            key, value = result_t.split(':', 1)
            result[key] = value

        return result


# -------------------------------------------------------------------------------


class SearchMblRoutingRule(BaseRoutingRule):
    name = 'SEARCH_MBL'

    @classmethod
    def build_request_option(cls, mbl_no) -> RequestOption:
        url = (
            f'{BASE_URL}/uiArp02Action/searchBillofLadingInformationList.do?tmlCd=USLGB&blNo={mbl_no}&'
            f'acssHis=USLGB,{USER_ID}'
        )

        return RequestOption(
            method=RequestOption.METHOD_GET,
            rule_name=cls.name,
            url=url,
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.html'

    def handle(self, response):
        scripts = response.css('script')
        result_match_rule = CssQueryResultExistMatchRule('::text')
        result_script = find_selector_from(scripts, rule=result_match_rule)

        result_script_text = result_script.css('::text').get()
        result_text = self._extract_result_text(text=result_script_text)
        result = self._transform_results_text_to_dict(result_text=result_text)

        if self._check_mbl_no_invalid(result=result):
            raise TerminalInvalidMblNoError()

        yield TerminalItem(
            mbl_no=result['blNo'],
            vessel=result['vslNm'],
            voyage=result['usrInVoyNo'],
        )

    @staticmethod
    def _check_mbl_no_invalid(result: Dict):
        if result['vldFlg'] == 'Y':
            return False
        elif result['vldFlg'] == 'N':
            return True
        else:
            raise TerminalResponseFormatError(reason=f'Unexpected mbl valid state: `{result["vldFlg"]}`')

    @staticmethod
    def _extract_result_text(text: str):
        pattern = re.compile(r'\s+var\s+result\s+=\s+\[\{?(?P<results_text>.*)\}?\].+')
        match = pattern.match(text)
        results_text = match.group('results_text')
        results_text = results_text.replace('"', '')

        return results_text

    @staticmethod
    def _transform_results_text_to_dict(result_text: str) -> Dict:
        """
        result_text form: 'key1:value1,key2:value2,...,keyN:valueN'
        """
        result = {}

        result_tuples = result_text.split(',')
        for result_t in result_tuples:
            key, value = result_t.split(':', 1)
            result[key] = value

        return result


# -------------------------------------------------------------------------------


class CssQueryResultExistMatchRule(BaseMatchRule):

    def __init__(self, css_query: str):
        self._css_query = css_query

    def check(self, selector: scrapy.Selector) -> bool:
        texts = selector.css(self._css_query).getall()

        for t in texts:
            if 'result' in t:
                return True
        return False

