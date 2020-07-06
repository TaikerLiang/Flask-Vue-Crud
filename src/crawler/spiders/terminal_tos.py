import dataclasses
from typing import Dict

import scrapy
from scrapy import Selector

from crawler.core_terminal.base_spiders import BaseTerminalSpider
from crawler.core_terminal.exceptions import TerminalResponseFormatError, TerminalInvalidContainerNoError
from crawler.core_terminal.items import DebugItem, BaseTerminalItem, TerminalItem
from crawler.core_terminal.request_helpers import RequestOption
from crawler.core_terminal.rules import RuleManager, BaseRoutingRule
from crawler.extractors.table_extractors import BaseTableLocator, TableExtractor, HeaderMismatchError

BASE_URL = 'https://voyagertrack.portsamerica.com'

USERNAME = 'hc89scooter'
PASSWORD = 'bd19841017'


@dataclasses.dataclass
class WarningMessage:
    msg: str


class TerminalTosSpider(BaseTerminalSpider):
    name = 'terminal_tos'

    def __init__(self, *args, **kwargs):
        super(TerminalTosSpider, self).__init__(*args, **kwargs)

        rules = [
            LoginRoutingRule(),
            MblDetailRoutingRule(),
            ContainerDetailRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)

    def start(self):
        request_option = LoginRoutingRule.build_request_option(container_no=self.container_no, mbl_no=self.mbl_no)
        yield self._build_request_by(option=request_option)

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
            elif isinstance(result, WarningMessage):
                self.logger.warning(msg=result.msg)
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


class LoginRoutingRule(BaseRoutingRule):
    name = 'LOGIN'

    @classmethod
    def build_request_option(cls, container_no, mbl_no) -> RequestOption:
        url = f'{BASE_URL}/logon'
        form_data = {
            'SiteId': 'WBCT_LA',
            'SiteName': 'WBCT Los Angeles',
            'ForTosPortalSite': 'False',
            'UserName': USERNAME,
            'Password': PASSWORD,
        }

        return RequestOption(
            method=RequestOption.METHOD_POST_FORM,
            rule_name=cls.name,
            url=url,
            form_data=form_data,
            meta={
                'container_no': container_no,
                'mbl_no': mbl_no,
            },
        )

    def handle(self, response):
        container_no = response.meta['container_no']
        mbl_no = response.meta['mbl_no']

        yield MblDetailRoutingRule.build_request_option(mbl_no=mbl_no)
        yield ContainerDetailRoutingRule.build_request_option(container_no=container_no)

    def get_save_name(self, response) -> str:
        return f'{self.name}.html'


class MblDetailRoutingRule(BaseRoutingRule):
    name = 'MBL_DETAIL'

    @classmethod
    def build_request_option(cls, mbl_no) -> RequestOption:
        url = f'{BASE_URL}/Report/ImportContainer/Inquiry?InquiryType=BillOfLading&BillOfLadingNumber={mbl_no}'

        return RequestOption(
            method=RequestOption.METHOD_GET,
            rule_name=cls.name,
            url=url,
            meta={'mbl_no': mbl_no},
        )

    def handle(self, response):
        mbl_no = response.meta['mbl_no']

        if self.__is_mbl_number_invalid(response=response):
            yield WarningMessage(msg=f'[{self.name}] ----- handle -> mbl_no is invalid : `{mbl_no}`')
            return

        mbl_detail = self.__extract_mbl_detail(response=response)
        yield TerminalItem(
            **mbl_detail,
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.html'

    @staticmethod
    def __is_mbl_number_invalid(response: scrapy.Selector) -> bool:
        error = response.css('div.error[style]')
        if error:
            return True
        else:
            return False

    def __extract_mbl_detail(self, response: scrapy.Selector) -> Dict:
        left_div_selector = response.css('div.inquiry-panel div.sub-form')[0]

        if left_div_selector is None:
            raise TerminalResponseFormatError(reason='Mbl detail left table not found')

        left_mbl_detail = self.__extract_div_text(div=left_div_selector)
        return {
            'vessel': left_mbl_detail['Vessel Name'] or None,
            'voyage': left_mbl_detail['Voyage Number'] or None,
        }

    @staticmethod
    def __extract_div_text(div: scrapy.Selector) -> Dict:
        title_text_list = div.css('div.display-label::text').getall()
        data_text_list = div.css('div.display-field::text').getall()

        return_dict = {}
        for title, data in zip(title_text_list, data_text_list):
            return_dict[title.strip()] = data.strip()

        return return_dict


class ContainerDetailRoutingRule(BaseRoutingRule):
    name = 'CONTAINER_DETAIL'

    @classmethod
    def build_request_option(cls, container_no) -> RequestOption:
        url = f'{BASE_URL}/Report/ImportContainer/Inquiry?InquiryType=ContainerNumber&ContainerNumber={container_no}'

        return RequestOption(
            method=RequestOption.METHOD_GET,
            rule_name=cls.name,
            url=url,
        )

    def handle(self, response):
        if self.__is_container_number_invalid(response=response):
            raise TerminalInvalidContainerNoError()

        container_info = self.__extract_container_info(response=response)

        yield TerminalItem(
            **container_info,
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.html'

    @staticmethod
    def __is_container_number_invalid(response: scrapy.Selector):
        error = response.css('div.clear.error')
        if error:
            return True
        else:
            return False

    @staticmethod
    def __extract_container_info(response: scrapy.Selector) -> Dict:
        table_selector = response.css('table.appointment')

        if table_selector is None:
            raise TerminalResponseFormatError(reason='container info table not found')

        table_locator = ContainerInfoTableLocator()
        table_locator.parse(table=table_selector)
        table = TableExtractor(table_locator=table_locator)

        for left in table_locator.iter_left_headers():
            return {
                'freight_release': table.extract_cell('Freight Status', left) or None,
                'customs_release': table.extract_cell('Customs Status', left) or None,
                'ready_for_pick_up': table.extract_cell('Available', left) or None,
                'appointment_date': table.extract_cell('Appointment Time', left) or None,
                'last_free_day': table.extract_cell('Last Free Day', left) or None,
                'demurrage': table.extract_cell('Demurrage Amount(Future)', left) or None,
                'container_no': table.extract_cell('Container Number', left) or None,
                'carrier': table.extract_cell('SSCO', left) or None,
                'container_spec': table.extract_cell('Type', left) or None,
                'holds': table.extract_cell('Misc. Holds', left) or None,
            }


class ContainerInfoTableLocator(BaseTableLocator):
    """
        +---------+---------+-----+---------+ <table>
        | Title 1 | Title 2 | ... | Title N | <tr>
        +---------+---------+-----+---------+
        | Data 1  | Data 2  | ... | Data N  | <tr>
        +---------+---------+-----+---------+ </table>
    """
    TR_TITLE_INDEX = 0
    TR_DATA_INDEX = 0

    def __init__(self):
        self._td_map = {}
        self._data_len = 0

    def parse(self, table: Selector):
        title_tr = table.css('thead tr')[self.TR_TITLE_INDEX]
        data_tr = table.css('tbody tr')[self.TR_DATA_INDEX]

        title_th_list = title_tr.css('th')
        title_text_list = []
        for th in title_th_list:
            th_text_list = th.css('::text').getall()
            title_text_list.append(''.join(map(str.strip, th_text_list)))

        for title_index, title_text in enumerate(title_text_list):
            data_index = title_index

            title_text = title_text.strip()
            self._td_map[title_text] = []

            data_td = data_tr.css('td')[data_index]

            self._td_map[title_text].append(data_td)

        first_title_text = title_text_list[0]
        self._data_len = len(self._td_map[first_title_text])

    def get_cell(self, top, left) -> Selector:
        try:
            return self._td_map[top][left]
        except KeyError as err:
            raise HeaderMismatchError(repr(err))

    def has_header(self, top=None, left=None) -> bool:
        return (top in self._td_map) and (left is None)

    def iter_left_headers(self):
        for index in range(self._data_len):
            yield index
