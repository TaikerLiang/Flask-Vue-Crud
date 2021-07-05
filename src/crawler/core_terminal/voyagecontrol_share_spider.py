import dataclasses
import json
import re
from typing import Dict, List

from scrapy import Request

from crawler.core_terminal.base import TERMINAL_RESULT_STATUS_FATAL
from crawler.core_terminal.base_spiders import BaseMultiTerminalSpider
from crawler.core_terminal.exceptions import BaseTerminalError, TerminalResponseFormatError
from crawler.core_terminal.items import (
    BaseTerminalItem,
    DebugItem,
    TerminalItem,
    ExportErrorData,
    InvalidContainerNoItem,
)
from crawler.core_terminal.rules import RuleManager, BaseRoutingRule, RequestOption


@dataclasses.dataclass
class CompanyInfo:
    lower_short: str
    upper_short: str
    email: str
    password: str


@dataclasses.dataclass
class WarningMessage:
    msg: str


class VoyagecontrolShareSpider(BaseMultiTerminalSpider):
    name = ''
    company_info = CompanyInfo(
        lower_short='',
        upper_short='',
        email='',
        password='',
    )

    def __init__(self, *args, **kwargs):
        super(VoyagecontrolShareSpider, self).__init__(*args, **kwargs)

        rules = [
            LoginRoutingRule(),
            AddContainerToTraceRoutingRule(),
            ListTracedContainerRoutingRule(),
            DelContainerFromTraceRoutingRule(),
            SearchMblRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)

    def start(self):
        unique_container_nos = list(self.cno_tid_map.keys())
        option = LoginRoutingRule.build_request_option(
            container_no_list=unique_container_nos, company_info=self.company_info
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
                if c_no:
                    t_ids = self.cno_tid_map[c_no]
                    for t_id in t_ids:
                        result['task_id'] = t_id
                        yield result
            elif isinstance(result, RequestOption):
                yield self._build_request_by(option=result)
            elif isinstance(result, WarningMessage):
                self.logger.warning(msg=result.msg)
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
        elif option.method == RequestOption.METHOD_POST_BODY:
            return Request(
                url=option.url,
                headers=option.headers,
                meta=meta,
                dont_filter=True,
                method='POST',
                body=option.body,
            )
        else:
            raise ValueError(f'Invalid option.method [{option.method}]')


# -------------------------------------------------------------------------------


class LoginRoutingRule(BaseRoutingRule):
    name = 'LOGIN'

    @classmethod
    def build_request_option(cls, container_no_list, company_info: CompanyInfo) -> RequestOption:
        url = f'https://{company_info.lower_short}.voyagecontrol.com/api/jwt/login/?venue={company_info.lower_short}'
        headers = {
            'Content-Type': 'application/json',
        }
        form_data = {
            'email': company_info.email,
            'password': company_info.password,
        }

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_POST_BODY,
            url=url,
            headers=headers,
            body=json.dumps(form_data),
            meta={
                'container_no_list': container_no_list,
                'company_info': company_info,
            },
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.json'

    def handle(self, response):
        container_no_list = response.meta['container_no_list']
        company_info = response.meta['company_info']

        response_json = json.loads(response.text)
        authorization_token = response_json['token']

        for container_no in container_no_list:
            yield ListTracedContainerRoutingRule.build_request_option(
                container_no=container_no,
                authorization_token=authorization_token,
                company_info=company_info,
                is_first=True,
            )

        # if mbl_no:
        #     yield SearchMblRoutingRule.build_request_option(mbl_no=mbl_no, token=authorization_token)


# -------------------------------------------------------------------------------


class ListTracedContainerRoutingRule(BaseRoutingRule):
    name = 'LIST_TRACED_CONTAINER'

    @classmethod
    def build_request_option(
        cls, container_no, authorization_token, company_info: CompanyInfo, is_first: bool = False
    ) -> RequestOption:
        url = f'https://{company_info.lower_short}.voyagecontrol.com/lynx/container/?venue={company_info.lower_short}'
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=url,
            headers={
                'authorization': 'JWT ' + authorization_token,
            },
            meta={
                'is_first': is_first,
                'container_no': container_no,
                'authorization_token': authorization_token,
                'company_info': company_info,
            },
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.json'

    def handle(self, response):
        is_first = response.meta['is_first']
        container_no = response.meta['container_no']
        authorization_token = response.meta['authorization_token']
        company_info = response.meta['company_info']

        response_json = json.loads(response.text)

        container = self.__get_container_from(response_json=response_json, container_no=container_no)

        if container:
            if is_first:
                # update existing container: delete -> add
                yield DelContainerFromTraceRoutingRule.build_request_option(
                    container_no=container_no,
                    authorization_token=authorization_token,
                    company_info=company_info,
                    not_finished=True,
                )

                return

            collated_container = self.__extract_container_info(container=container)
            print('Taiker-1 TerminalItem', collated_container['container_no'])
            yield TerminalItem(**collated_container)

            yield DelContainerFromTraceRoutingRule.build_request_option(
                container_no=container_no, authorization_token=authorization_token, company_info=company_info
            )

        else:
            yield AddContainerToTraceRoutingRule.build_request_option(
                container_no=container_no, authorization_token=authorization_token, company_info=company_info
            )

    @staticmethod
    def __get_container_from(response_json: Dict, container_no: str):
        containers = response_json['rows']

        for container in containers:
            if container_no == container['containerId']:
                return container

        return None

    @staticmethod
    def __is_container_exist(container_no: str, response_json: Dict) -> bool:
        rows = response_json['rows']

        for container in rows:
            if container_no == container['containerId']:
                return True

        return False

    def __extract_container_info(self, container: Dict) -> Dict:
        print('container', container)
        status_name = container['containerStatus']['name']
        container_status = self.__extract_container_status(contain_container_status=status_name)

        return {
            'container_no': container['containerId'],
            'ready_for_pick_up': container_status,
            'appointment_date': container['status'].get('APPOINTMENT_HOLD', ''),
            'last_free_day': container['status'].get('PORT_LFD', ''),
            'demurrage': container['status'].get('DEMURRAGE', ''),
            'holds': container['status'].get('HOLD_INFO', ''),
            'cy_location': container['status'].get('LOCATIONDETAILS', ''),
            # release information might be elsewhere(i.e. container inquiry) for fenix
            'customs_release': container['status'].get('CUSTOMS', ''),
            'carrier_release': container['status'].get('FREIGHT', ''),
        }

    @staticmethod
    def __extract_container_status(contain_container_status):
        pattern = re.compile(r'CONTAINER_STATUS_(?P<container_status>\w+)')
        match = pattern.match(contain_container_status)

        return match.group('container_status')


# -------------------------------------------------------------------------------


class AddContainerToTraceRoutingRule(BaseRoutingRule):
    name = 'ADD_CONTAINER_TO_TRACE'

    @classmethod
    def build_request_option(cls, container_no, authorization_token, company_info: CompanyInfo) -> RequestOption:
        url = f'https://{company_info.lower_short}.voyagecontrol.com/lynx/container/ids/insert?venue={company_info.lower_short}'
        headers = {
            'Content-Type': 'application/json',
            'authorization': 'JWT ' + authorization_token,
        }
        form_data = {
            'containerIds': [container_no],
        }

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_POST_BODY,
            url=url,
            headers=headers,
            body=json.dumps(form_data),
            meta={
                'container_no': container_no,
                'authorization_token': authorization_token,
                'dont_retry': True,
                'handle_httpstatus_list': [502],
                'company_info': company_info,
            },
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.html'

    def handle(self, response):
        container_no = response.meta['container_no']
        authorization_token = response.meta['authorization_token']
        company_info = response.meta['company_info']

        # 502: add invalid container_no into container_traced_list
        # 200: add valid container_no into container_traced_list
        if response.status == 502:
            return InvalidContainerNoItem()
        elif response.status != 200:
            raise VoyagecontrolResponseStatusCodeError(
                reason=f'AddContainerToTraceRoutingRule: Unexpected status code: `{response.status}`'
            )

        yield ListTracedContainerRoutingRule.build_request_option(
            container_no=container_no, authorization_token=authorization_token, company_info=company_info
        )


# -------------------------------------------------------------------------------


class DelContainerFromTraceRoutingRule(BaseRoutingRule):
    name = 'DEL_CONTAINER_FROM_TRACE'

    @classmethod
    def build_request_option(
        cls, container_no, authorization_token, company_info: CompanyInfo, not_finished: bool = False
    ) -> RequestOption:
        url = f'https://{company_info.lower_short}.voyagecontrol.com/lynx/container/ids/delete?venue={company_info.lower_short}'
        headers = {
            'Content-Type': 'application/json',
            'authorization': 'JWT ' + authorization_token,
        }
        form_data = {
            "containerIds": [container_no],
            "bookingRefs": [None],
        }

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_POST_BODY,
            url=url,
            headers=headers,
            body=json.dumps(form_data),
            meta={
                'container_no': container_no,
                'authorization_token': authorization_token,
                'not_finished': not_finished,
                'company_info': company_info,
            },
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.html'

    def handle(self, response):
        container_no = response.meta['container_no']
        authorization_token = response.meta['authorization_token']
        not_finished = response.meta['not_finished']
        company_info = response.meta['company_info']

        if response.status != 200:
            raise VoyagecontrolResponseStatusCodeError(
                reason=f'DelContainerFromTraceRoutingRule: Unexpected status code: `{response.status}`'
            )

        if not_finished:
            yield AddContainerToTraceRoutingRule.build_request_option(
                container_no=container_no, authorization_token=authorization_token, company_info=company_info
            )
        else:
            # because of parse(), need to yield empty item
            print('Taiker-2 TerminalItem')
            yield TerminalItem(container_no='')


# -------------------------------------------------------------------------------


class SearchMblRoutingRule(BaseRoutingRule):
    name = 'SEARCH_MBL'

    @classmethod
    def build_request_option(cls, mbl_no, token, company_info: CompanyInfo) -> RequestOption:
        url = f'https://{company_info.lower_short}.voyagecontrol.com/api/bookings_inquiry/landingbill/?param={mbl_no}&venue={company_info.lower_short}'
        headers = {
            'Content-Type': 'application/json',
            'authorization': 'JWT ' + token,
        }

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=url,
            headers=headers,
            meta={
                'handle_httpstatus_list': [404],
                'mbl_no': mbl_no,
                'company_info': company_info,
            },
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.json'

    def handle(self, response):
        mbl_no = response.meta['mbl_no']
        company_info = response.meta['company_info']

        if response.status == 404:
            # we want to log this error msg, but we don't want close spider, so we don't raise an exception.
            yield WarningMessage(msg=f'[{self.name}] ----- handle -> mbl_no is invalid : `{mbl_no}`')
            return

        response_json = json.loads(response.text)

        self.__check_format(response_json=response_json)

        mbl_info = self.__extract_mbl_info(response_json=response_json)
        print('Taiker-3 TerminalItem')
        yield TerminalItem(container='', **mbl_info)

    @staticmethod
    def __check_format(response_json: Dict):
        bill_of_health = response_json['bill_of_health']
        data_table = response_json['bill_of_health']['query-response']['data-table']

        if len(bill_of_health) == 1 and 'lineStatus' not in bill_of_health:
            pass
        elif len(bill_of_health) == 2 and 'lineStatus' in bill_of_health:
            pass
        else:
            raise TerminalResponseFormatError(reason=f'Unexpected bill_of_health format: `{bill_of_health}`')

        if len(data_table) != 4:
            raise TerminalResponseFormatError(reason=f'Unexpected data-table format: `{data_table}`')

        if len(data_table['columns']['column']) == 12 and len(data_table['rows']['row']['field']) == 12:
            return

        raise TerminalResponseFormatError(reason=f'Unexpected data-table format: `{data_table}`')

    @staticmethod
    def __extract_mbl_info(response_json: Dict) -> Dict:
        bill_of_health = response_json['bill_of_health']
        data_table = bill_of_health['query-response']['data-table']
        title = data_table['columns']['column']
        data = data_table['rows']['row']['field']

        mbl_info_dict = {}
        for key, value in zip(title, data):
            mbl_info_dict[key] = value

        line_status = None
        if 'lineStatus' in bill_of_health:
            line_status = bill_of_health['lineStatus'].get('@id')

        return {
            'freight_release': line_status if line_status else 'Released',
            # hard code here, we don't find the other value.
            'customs_release': 'Released',
            'carrier': mbl_info_dict['Line Op'],
            'mbl_no': mbl_info_dict['BL Nbr'],
            'voyage': mbl_info_dict['Ves. Visit'],
        }


# -------------------------------------------------------------------------------


class VoyagecontrolResponseStatusCodeError(BaseTerminalError):
    status = TERMINAL_RESULT_STATUS_FATAL

    def __init__(self, reason: str):
        self.reason = reason

    def build_error_data(self):
        return ExportErrorData(status=self.status, detail=f'<status-code-error> {self.reason}')
