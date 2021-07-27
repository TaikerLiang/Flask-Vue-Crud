import io
import random
import re

import scrapy
from scrapy.http import HtmlResponse
import PIL.Image as Image
from anticaptchaofficial.imagecaptcha import *

from crawler.core_terminal.base_spiders import BaseMultiTerminalSpider
from crawler.core_terminal.items import DebugItem, TerminalItem, InvalidContainerNoItem
from crawler.core_terminal.request_helpers import RequestOption
from crawler.core_terminal.rules import RuleManager, BaseRoutingRule

BASE_URL = 'https://www.etslink.com'
EMAIL = 'w87818@yahoo.com.tw'
PASSWORD = 'Bb1234567890'


class TerminalEtsSpider(BaseMultiTerminalSpider):
    firms_code = 'Y124'
    name = 'terminal_ets'

    def __init__(self, *args, **kwargs):
        super(TerminalEtsSpider, self).__init__(*args, **kwargs)

        rules = [
            MainPageRoutingRule(),
            CaptchaRoutingRule(),
            LoginRoutingRule(),
            ContainerRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)

    def start(self):
        unique_container_nos = list(self.cno_tid_map.keys())
        option = MainPageRoutingRule.build_request_option(container_no_list=unique_container_nos)
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
    def build_request_option(cls, container_no_list) -> RequestOption:
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=f'{BASE_URL}',
            meta={'container_no_list': container_no_list},
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.html'

    def handle(self, response):
        container_no_list = response.meta['container_no_list']

        verify_key = self._extract_verify_key(response=response)

        yield CaptchaRoutingRule.build_request_option(verify_key, container_no_list)

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
    def build_request_option(cls, verify_key, container_no_list) -> RequestOption:
        dc = cls._get_random_number()

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=f'{BASE_URL}/waut/VerifyCodeImage.jsp?dc={dc}&verifyKey={verify_key}',
            meta={'container_no_list': container_no_list, 'dc': dc, 'verify_key': verify_key},
        )

    def handle(self, response):
        container_no_list = response.meta['container_no_list']
        dc = response.meta['dc']
        verify_key = response.meta['verify_key']

        captcha_text = self._get_captcha_str(response.body)

        if captcha_text:
            yield LoginRoutingRule.build_request_option(
                captcha_text=captcha_text, container_no_list=container_no_list, dc=dc, verify_key=verify_key
            )
        else:
            yield LoginRoutingRule.build_request_option(
                captcha_text='', container_no_list=container_no_list, dc='', verify_key=verify_key
            )

    @staticmethod
    def _get_captcha_str(captcha_code):
        file_name = 'captcha.jpeg'
        image = Image.open(io.BytesIO(captcha_code))
        image.save(file_name)
        # api_key = 'f7dd6de6e36917b41d05505d249876c3'
        api_key='fbe73f747afc996b624e8d2a95fa0f84'
        solver = imagecaptcha()
        solver.set_verbose(1)
        solver.set_key(api_key)

        captcha_text = solver.solve_and_return_solution(file_name)
        if captcha_text != 0:
            return captcha_text
        else:
            print("task finished with error ", solver.error_code)
            return ''

    @staticmethod
    def _get_random_number():
        return str(int(random.random() * 10000000))


class LoginRoutingRule(BaseRoutingRule):
    name = 'LOGIN'

    @classmethod
    def build_request_option(cls, container_no_list, captcha_text, dc, verify_key) -> RequestOption:
        form_data = {
            'PI_LOGIN_ID': EMAIL,
            'PI_PASSWORD': PASSWORD,
            'PI_VERIFY_CODE': captcha_text,
            'PI_VERIFY_DC': dc,
            'PI_VERIFY_KEY': verify_key,
        }

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_POST_FORM,
            url=f'{BASE_URL}/login',
            form_data=form_data,
            meta={'container_no_list': container_no_list},
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.json'

    def handle(self, response):
        container_no_list = response.meta['container_no_list']

        response_dict = json.loads(response.text)
        sk = response_dict['_sk']

        yield ContainerRoutingRule.build_request_option(container_no_list=container_no_list, sk=sk)


class ContainerRoutingRule(BaseRoutingRule):
    name = 'CONTAINER'

    @classmethod
    def build_request_option(cls, container_no_list, sk) -> RequestOption:
        form_data = {
            'PI_BUS_ID': '?cma_bus_id',
            'PI_TMNL_ID': '?cma_env_loc',
            'PI_CTRY_CODE': '?cma_env_ctry',
            'PI_STATE_CODE': '?cma_env_state',
            'PI_CNTR_NO': '\n'.join(container_no_list),
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
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.json'

    def handle(self, response):
        container_info_list = self._extract_container_info(response=response)

        for container_info in container_info_list:
            if container_info['PO_TERMINAL_NAME'] == '<i>Record was not found!</i>':
                c_no = re.sub('<.*?>', '', container_info['PO_CNTR_NO'])
                yield InvalidContainerNoItem(
                    container_no=c_no,
                )
            else:
                yield TerminalItem(
                    container_no=container_info['PO_CNTR_NO'],
                    ready_for_pick_up=container_info['PO_AVAILABLE_IND'],
                    customs_release=container_info['PO_USA_STATUS'],
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
                    # extra field name
                    service=container_info['PO_SVC_QFR_DESC'],
                    carrier_release=container_info['PO_CARRIER_STATUS'],
                    tmf=container_info['PO_TMF_STATUS'],
                    demurrage_status=container_info['PO_DM_STATUS'],
                    # not on html
                    freight_release=container_info['PO_FR_STATUS'],  # not sure
                )

    @staticmethod
    def _extract_container_info(response: HtmlResponse):
        response_dict = json.loads(response.text)

        container_info_list = []
        titles = response_dict['cols']
        for resp in response_dict['data']:
            container_info = {}
            for title_index, title in enumerate(titles):
                data_index = title_index

                title_name = title['name']
                container_info[title_name] = resp[data_index]
            container_info_list.append(container_info)

        return container_info_list
