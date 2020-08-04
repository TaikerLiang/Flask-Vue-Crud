import io
import json
import random
import re

import scrapy
from python_anticaptcha import AnticaptchaClient, ImageToTextTask
from scrapy.http import HtmlResponse

from crawler.core_terminal.base_spiders import BaseTerminalSpider
from crawler.core_terminal.items import DebugItem, BaseTerminalItem, TerminalItem
from crawler.core_terminal.request_helpers import RequestOption
from crawler.core_terminal.rules import RuleManager, BaseRoutingRule

BASE_URL = 'https://www.etslink.com'
EMAIL = 'w87818@yahoo.com.tw'
PASSWORD = 'Aa1234567890'


class TerminalEtsSpider(BaseTerminalSpider):
    name = 'terminal_ets'

    def __init__(self, *args, **kwargs):
        super(TerminalEtsSpider, self).__init__(*args, **kwargs)

        rules = [
            MainPageRoutingRule(),
            CaptchaRoutingRule(),
            LoginRoutingRule(),
            ContainerRoutingRule(),
            MblRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)

    def start(self):
        option = MainPageRoutingRule.build_request_option(container_no=self.container_no)
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


class MainPageRoutingRule(BaseRoutingRule):
    name = 'MAIN_PAGE'

    @classmethod
    def build_request_option(cls, container_no) -> RequestOption:
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=f'{BASE_URL}',
            meta={'container_no': container_no},
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.html'

    def handle(self, response):
        container_no = response.meta['container_no']

        verify_key = self._extract_verify_key(response=response)

        yield CaptchaRoutingRule.build_request_option(verify_key, container_no)

    @staticmethod
    def _extract_verify_key(response: scrapy.Selector) -> str:
        pattern = re.compile(r'&verifyKey=(?P<verify_key>\d+)"')

        script_text = response.css('script').getall()[3]
        s = pattern.search(script_text)
        verify_key = s.group('verify_key')

        return verify_key


class CaptchaRoutingRule(BaseRoutingRule):
    name = 'CAPTCHA'

    @classmethod
    def build_request_option(cls, verify_key, container_no) -> RequestOption:
        dc = cls._get_random_number()
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=f'{BASE_URL}/waut/VerifyCodeImage.jsp?dc={dc}&verifyKey={verify_key}',
            meta={'container_no': container_no, 'dc': dc, 'verify_key': verify_key},
        )

    def get_save_name(self, response) -> str:
        pass

    def handle(self, response):
        container_no = response.meta['container_no']
        dc = response.meta['dc']
        verify_key = response.meta['verify_key']

        captcha = self._get_captcha_str(response.body)

        yield LoginRoutingRule.build_request_option(
            captcha=captcha, container_no=container_no, dc=dc, verify_key=verify_key)

    @staticmethod
    def _get_captcha_str(captcha_code):
        api_key = 'fbe73f747afc996b624e8d2a95fa0f84'
        captcha_fp = io.BytesIO(captcha_code)
        client = AnticaptchaClient(api_key)
        task = ImageToTextTask(captcha_fp)
        job = client.createTask(task)
        job.join()
        return job.get_captcha_text()

    @staticmethod
    def _get_random_number():
        return str(int(random.random() * 10000000))


class LoginRoutingRule(BaseRoutingRule):
    name = 'LOGIN'

    @classmethod
    def build_request_option(cls, captcha, container_no, dc, verify_key) -> RequestOption:
        form_data = {
            'PI_LOGIN_ID': EMAIL,
            'PI_PASSWORD': PASSWORD,
            'PI_VERIFY_CODE': captcha,
            'PI_VERIFY_DC': dc,
            'PI_VERIFY_KEY': verify_key,
        }

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_POST_FORM,
            url=f'{BASE_URL}/login',
            form_data=form_data,
            meta={'container_no': container_no},
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.json'

    def handle(self, response):
        container_no = response.meta['container_no']

        response_dict = json.loads(response.text)
        sk = response_dict['_sk']

        yield ContainerRoutingRule.build_request_option(container_no=container_no, sk=sk)


class ContainerRoutingRule(BaseRoutingRule):
    name = 'CONTAINER'

    @classmethod
    def build_request_option(cls, container_no, sk) -> RequestOption:
        form_data = {
            'PI_BUS_ID': '?cma_bus_id',
            'PI_TMNL_ID': '?cma_env_loc',
            'PI_CTRY_CODE': '?cma_env_ctry',
            'PI_STATE_CODE': '?cma_env_state',
            'PI_CNTR_NO': container_no,
            '_sk': sk,
            'page': '1',
            'start': '0',
            'limit': '-1',
        }

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_POST_FORM,
            url=f'{BASE_URL}/data/WIMPP003.queryByCntr.data.json?',
            form_data=form_data,
            meta={'container_no': container_no, 'sk': sk},
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.json'

    def handle(self, response):
        container_no = response.meta['container_no']
        sk = response.meta['sk']

        container_info = self.__extract_container_info(response=response)

        yield TerminalItem(
            container_no=container_info['PO_CNTR_NO'],
            ready_for_pick_up=container_info['PO_AVAILABLE_IND'],
            appointment_date=container_info['PO_APPOINTMENT_TIME'],
            last_free_day=container_info['PO_DM_LAST_FREE_DATE'],
            demurrage=container_info['PO_DM_AMT_DUE'],
            carrier=container_info['PO_CARRIER_SCAC_CODE'],
            container_spec=(
                f'{container_info["PO_CNTR_TYPE_S"]}/{container_info["PO_CNTR_TYPE_T"]}/'
                f'{container_info["PO_CNTR_TYPE_H"]}'
            ),
            holds=container_info['PO_TMNL_HOLD_IND'],
            cy_location=container_info['PO_YARD_LOC'],

        )

        sys_no = container_info['PO_MFSMS_SYSNO']
        yield MblRoutingRule.build_request_option(container_no=container_no, sys_no=sys_no, sk=sk)

    @staticmethod
    def __extract_container_info(response: HtmlResponse):
        response_dict = json.loads(response.text)

        titles = response_dict['cols']
        first_container_data = response_dict['data'][0]

        container_info = {}
        for title_index, title in enumerate(titles):
            data_index = title_index

            title_name = title['name']
            container_info[title_name] = first_container_data[data_index]

        return container_info


class MblRoutingRule(BaseRoutingRule):
    name = 'MBL'

    @classmethod
    def build_request_option(cls, container_no, sys_no, sk) -> RequestOption:
        form_data = {
            'PI_BUS_ID': '?cma_bus_id',
            'PI_TMNL_ID': 'LAX',
            'PI_CTRY_CODE': '?cma_env_ctry',
            'PI_STATE_CODE': '?cma_env_state',
            'PI_MFSMS_SYSNO': sys_no,
            'PI_CNTR_NO': container_no,
            '_sk': sk,
            'page': '1',
            'start': '0',
            'limit': '-1',
        }

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_POST_FORM,
            url=f'https://www.etslink.com/data/WIMPP003.queryBlnoByCntr.data.json?',
            form_data=form_data,
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.json'

    def handle(self, response):
        mbl_info = self.__extract_mbl_info(response=response)

        vessel, voyage = mbl_info['PO_VSLVOY'].split('/')

        yield TerminalItem(
            vessel=vessel,
            mbl_no=mbl_info['PO_BL_NO'],
            voyage=voyage,
        )

    @staticmethod
    def __extract_mbl_info(response: scrapy.Selector):
        response_dict = json.loads(response.text)

        titles = response_dict['cols']
        first_container_data = response_dict['data'][0]

        mbl_info = {}
        for title_index, title in enumerate(titles):
            data_index = title_index

            title_name = title['name']
            mbl_info[title_name] = first_container_data[data_index]

        return mbl_info


