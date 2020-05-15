import datetime
from typing import Dict

import scrapy
from scrapy import Selector

from crawler.core_terminal.base_spiders import BaseTerminalSpider
from crawler.core_terminal.exceptions import TerminalResponseFormatError
from crawler.core_terminal.items import BaseTerminalItem, DebugItem, TerminalItem
from crawler.core_terminal.request_helpers import RequestOption
from crawler.core_terminal.rules import RuleManager, BaseRoutingRule
from crawler.extractors.table_cell_extractors import BaseTableCellExtractor
from crawler.extractors.table_extractors import BaseTableLocator, HeaderMismatchError, TableExtractor

BASE_URL = 'https://tms.itslb.com'
USER_NAME = 'BrianLee'
PASSWORD = 'ZD_uSUFMy!6Nfu'


class SharedSpider(BaseTerminalSpider):
    name = None
    terminal_id = None

    def __init__(self, *args, **kwargs):
        super(SharedSpider, self).__init__(*args, **kwargs)

        rules = [
            TokenRoutingRule(),
            LoginRoutingRule(terminal_id=self.terminal_id),
            SetTerminalRoutingRule(),
            ContainerAvailabilityRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)

    def start(self):
        request_option = TokenRoutingRule.build_request_option(container_no=self.container_no)
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
            else:
                raise RuntimeError()

    def _build_request_by(self, option: RequestOption):
        meta = {
            RuleManager.META_TERMINAL_CORE_RULE_NAME: option.rule_name,
            **option.meta,
        }

        if option.method == RequestOption.METHOD_GET:
            return scrapy.Request(
                url=option.url,
                headers=option.headers,
                meta=meta,
            )
        elif option.method == RequestOption.METHOD_POST_FORM:
            return scrapy.FormRequest(
                url=option.url,
                headers=option.headers,
                meta=meta,
                formdata=option.form_data,
            )
        else:
            raise ValueError(f'Invalid option.method [{option.method}]')


class TerminalTmsLongBeachSpider(SharedSpider):
    name = 'terminal_tms_long_beach'
    terminal_id = 1


class TerminalTmsHuskySpider(SharedSpider):
    terminal_id = 3
    name = 'terminal_tms_husky'


class TokenRoutingRule(BaseRoutingRule):
    name = 'TOKEN'

    @classmethod
    def build_request_option(cls, container_no) -> RequestOption:
        url = f'{BASE_URL}/tms2/Account/Login'

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=url,
            meta={'container_no': container_no},
        )
    
    def handle(self, response):
        container_no = response.meta['container_no']

        token = self._get_token(response=response)

        yield LoginRoutingRule.build_request_option(token=token, container_no=container_no)

    def get_save_name(self, response):
        return f'{self.name}.html'

    @staticmethod
    def _get_token(response: scrapy.Selector) -> str:
        token = response.css('form input::attr(value)').get()
        return token


class LoginRoutingRule(BaseRoutingRule):
    name = 'LOGIN'

    def __init__(self, terminal_id):
        self.terminal_id = terminal_id

    @classmethod
    def build_request_option(cls, token, container_no) -> RequestOption:
        url = f'{BASE_URL}/tms2/Account/Login?ReturnUrl=%2Ftms2%2FImport%2FContainerAvailability'
        form_data = {
            '__RequestVerificationToken': token,
            'UserName': USER_NAME,
            'Password': PASSWORD,
        }

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_POST_FORM,
            url=url,
            form_data=form_data,
            meta={'container_no': container_no},
        )

    def handle(self, response):
        container_no = response.meta['container_no']

        set_terminal_token = self._get_set_terminal_token(response=response)
        container_availability_token = self._get_container_availability(response=response)

        current_terminal_id = self._get_current_terminal_id(response=response)
        if self.terminal_id == current_terminal_id:
            yield ContainerAvailabilityRoutingRule.build_request_option(
                token=container_availability_token, container_no=container_no)
        else:
            yield SetTerminalRoutingRule.build_request_option(
                set_terminal_token=set_terminal_token,
                container_availability_token=container_availability_token,
                container_no=container_no,
            )

    def get_save_name(self, response):
        return f'{self.name}.html'

    @staticmethod
    def _get_set_terminal_token(response: scrapy.Selector) -> str:
        token = response.css('form[id="TerminalForm"] input::attr(value)').get()
        return token

    @staticmethod
    def _get_container_availability(response: scrapy.Selector) -> str:
        token = response.css('form[id="formAvailabilityHeader"] input::attr(value)').get()
        return token

    @staticmethod
    def _get_current_terminal_id(response: scrapy.Selector) -> str:
        terminal_id = response.css('select option[selected]::attr(value)').get()
        return terminal_id


class SetTerminalRoutingRule(BaseRoutingRule):
    name = 'SET_TERMINAL'

    @classmethod
    def build_request_option(cls, set_terminal_token, container_availability_token, container_no) -> RequestOption:
        url = f'{BASE_URL}/tms2/Account/SetTerminal'
        form_data = {
            '__RequestVerificationToken': set_terminal_token,
            'loginTerminalId': '3',
        }

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_POST_FORM,
            url=url,
            form_data=form_data,
            meta={
                'container_availability_token': container_availability_token,
                'container_no': container_no,
            },
        )

    def handle(self, response):
        container_no = response.meta['container_no']
        token = response.meta['container_availability_token']

        yield ContainerAvailabilityRoutingRule.build_request_option(token=token, container_no=container_no)

    def get_save_name(self, response):
        return f'{self.name}.html'


class ContainerAvailabilityRoutingRule(BaseRoutingRule):
    name = 'CONTAINER_AVAILABILITY'

    @classmethod
    def build_request_option(cls, token, container_no) -> RequestOption:
        url = f'{BASE_URL}/tms2/Import/ContainerAvailability'
        yesterday_date_text = cls._get_yesterday_date()
        form_data = {
            '__RequestVerificationToken': token,
            'pickupDate': yesterday_date_text,
            'refNums': container_no,
            'refType': 'CN',  # TODO: remind Yoyo to modify document
        }

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_POST_FORM,
            url=url,
            form_data=form_data,
            meta={'container_no': container_no,},
        )

    def handle(self, response):
        container_info = self._extract_container_info(response=response)
        extra_container_info = self._extract_extra_container_info(response=response)

        yield TerminalItem(
            container_no=container_info['container_no'],
            freight_release=extra_container_info['freight_release'],
            customs_release=extra_container_info['customs_release'],
            discharge_date=container_info['discharge_date'],
            ready_for_pick_up=container_info['ready_for_pick_up'],
            last_free_day=container_info['last_free_day'],
            demurrage=extra_container_info['demurrage'],
            carrier=container_info['carrier'],
            container_spec=container_info['container_spec'],
            vessel=extra_container_info['vessel'],
            mbl_no=extra_container_info['mbl_no'],
            voyage=extra_container_info['voyage'],
            chassis_no=container_info['chassis_no'],
        )

    def get_save_name(self, response):
        container_no = response.meta['container_no']
        return f'{self.name}_{container_no}.html'

    @staticmethod
    def _get_yesterday_date() -> str:
        yesterday_date_time = datetime.datetime.today() - datetime.timedelta(days=1)
        yesterday_date_text = yesterday_date_time.strftime('%m/%d/%Y')

        return yesterday_date_text

    @staticmethod
    def _extract_container_info(response: scrapy.Selector) -> Dict:
        table_selector = response.css('table.table-borderless')

        if table_selector is None:
            raise TerminalResponseFormatError(reason='Container info table not found')

        table_locator = TopInfoTableLocator()
        table_locator.parse(table=table_selector)
        table = TableExtractor(table_locator=table_locator)

        for left in table_locator.iter_left_headers():
            return {
                'discharge_date': table.extract_cell('Dschg Date', left),
                'ready_for_pick_up': table.extract_cell('Pick Up', left),
                'last_free_day': table.extract_cell('LFD', left),
                'container_no': table.extract_cell('Container#', left, TdSpanExtractor()),
                'carrier': table.extract_cell('Line', left),
                'container_spec': table.extract_cell('SzTpHt', left),
                'chassis_no': table.extract_cell('Chassis#', left),
            }

    @staticmethod
    def _extract_extra_container_info(response: scrapy.Selector) -> Dict:
        table_selector = response.css('table.table-bordered')

        if table_selector is None:
            raise TerminalResponseFormatError(reason='Extra container info table not found')

        left_table_locator = LeftBottomInfoLocator()
        left_table_locator.parse(table=table_selector)
        left_table = TableExtractor(table_locator=left_table_locator)

        middle_table_locator = MiddleBottomInfoLocator()
        middle_table_locator.parse(table=table_selector)
        middle_table = TableExtractor(table_locator=middle_table_locator)

        right_table_locator = RightBottomInfoLocator()
        right_table_locator.parse(table=table_selector)
        right_table = TableExtractor(table_locator=right_table_locator)

        return {
            'vessel': left_table.extract_cell(None, 'Vessel'),
            'customs_release': left_table.extract_cell(None, 'Customs'),
            'freight_release': left_table.extract_cell(None, 'Freight'),
            'voyage': middle_table.extract_cell(None, 'Voyage'),
            'mbl_no': right_table.extract_cell(None, 'B/L#'),
            'demurrage': right_table.extract_cell(None, 'Demurrage'),
        }


class TopInfoTableLocator(BaseTableLocator):

    """
        +---------+---------+-----+---------+ <table>
        | Title 1 | Title 2 | ... | Title N | <tr>
        +---------+---------+-----+---------+
        | Data 1  | Data 2  | ... | Data N  | <tr>
        +---------+---------+-----+---------+
        | extra container info table        | <tr>
        +-----------------------------------+ </table>
    """

    TR_TITLE_INDEX = 0
    TR_DATA_INDEX_BEGIN = 1
    TR_DATA_INDEX_END = 2

    def __init__(self):
        self._td_map = {}
        self._data_len = 0

    def parse(self, table: Selector):
        title_tr = table.css('tr')[self.TR_TITLE_INDEX]
        data_tr_list = table.css('tr')[self.TR_DATA_INDEX_BEGIN: self.TR_DATA_INDEX_END]

        title_text_list = title_tr.css('th a::text').getall()

        for title_index, title_text in enumerate(title_text_list):
            data_index = title_index

            title_text = title_text.strip()
            self._td_map[title_text] = []

            for data_tr in data_tr_list:
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


class TdSpanExtractor(BaseTableCellExtractor):

    def extract(self, cell: Selector) -> str:
        td_text = cell.css('span::text').get()
        return td_text.strip() if td_text else ''


class LeftBottomInfoLocator(BaseTableLocator):

    """
        +---------+--------+-----+-----+-----+-----+ <table>
        | Title 1 | Data 1 |     |     |     |     | <tr>
        +---------+--------+-----+-----+-----+-----+
        | Title 2 | Data 2 |     |     |     |     | <tr>
        +---------+--------+-----+-----+-----+-----+
        | ...     | ...    |     |     |     |     | <tr>
        +---------+--------+-----+-----+-----+-----+
        | Title N | Data N |     |     |     |     | <tr>
        +---------+--------+-----+-----+-----+-----+ </table>
    """

    TR_CONTENT_BEGIN_INDEX = 0
    TD_TITLE_INDEX = 0
    TD_DATA_INDEX = 1

    def __init__(self):
        self._td_map = {}

    def parse(self, table: scrapy.Selector):
        content_tr_list = table.css('tr')[self.TR_CONTENT_BEGIN_INDEX:]

        for tr in content_tr_list:
            title_td = tr.css('td')[self.TD_TITLE_INDEX]
            data_td = tr.css('td')[self.TD_DATA_INDEX]

            title_text = title_td.css('::text').get().strip()

            self._td_map[title_text] = data_td

    def get_cell(self, top, left) -> scrapy.Selector:
        assert top is None
        try:
            return self._td_map[left]
        except KeyError as err:
            raise HeaderMismatchError(repr(err))

    def has_header(self, top=None, left=None) -> bool:
        return (top is None) and (left in self._td_map)


class MiddleBottomInfoLocator(BaseTableLocator):

    """
        +-----+-----+---------+--------+-----+-----+ <table>
        |     |     | Title 1 | Data 1 |     |     | <tr>
        +-----+-----+---------+--------+-----+-----+
        |     |     | Title 2 | Data 2 |     |     | <tr>
        +-----+-----+---------+--------+-----+-----+
        |     |     | ...     | ...    |     |     | <tr>
        +-----+-----+---------+--------+-----+-----+
        |     |     | Title N | Data N |     |     | <tr>
        +-----+-----+---------+--------+-----+-----+ </table>
    """

    TR_CONTENT_BEGIN_INDEX = 0
    TR_CONTENT_END_INDEX = 3
    TD_TITLE_INDEX = 2
    TD_DATA_INDEX = 3

    def __init__(self):
        self._td_map = {}

    def parse(self, table: scrapy.Selector):
        content_tr_list = table.css('tr')[self.TR_CONTENT_BEGIN_INDEX:self.TR_CONTENT_END_INDEX]

        for tr in content_tr_list:
            title_td = tr.css('td')[self.TD_TITLE_INDEX]
            data_td = tr.css('td')[self.TD_DATA_INDEX]

            title_text = title_td.css('::text').get().strip()

            self._td_map[title_text] = data_td

    def get_cell(self, top, left) -> scrapy.Selector:
        assert top is None
        try:
            return self._td_map[left]
        except KeyError as err:
            raise HeaderMismatchError(repr(err))

    def has_header(self, top=None, left=None) -> bool:
        return (top is None) and (left in self._td_map)


class RightBottomInfoLocator(BaseTableLocator):

    """
        +-----+-----+-----+-----+---------+--------+ <table>
        |     |     |     |     | Title 1 | Data 1 | <tr>
        +-----+-----+-----+-----+---------+--------+
        |     |     |     |     | Title 2 | Data 2 | <tr>
        +-----+-----+-----+-----+---------+--------+
        |     |     |     |     | ...     | ...    | <tr>
        +-----+-----+-----+-----+---------+--------+
        |     |     |     |     | Title N | Data N | <tr>
        +-----+-----+-----+-----+---------+--------+ </table>
    """

    TR_CONTENT_BEGIN_INDEX = 0
    TR_CONTENT_END_INDEX = 4
    TD_TITLE_INDEX = 4
    TD_DATA_INDEX = 5

    def __init__(self):
        self._td_map = {}

    def parse(self, table: scrapy.Selector):
        content_tr_list = table.css('tr')[self.TR_CONTENT_BEGIN_INDEX:self.TR_CONTENT_END_INDEX]

        for tr in content_tr_list:
            title_td = tr.css('td')[self.TD_TITLE_INDEX]
            data_td = tr.css('td')[self.TD_DATA_INDEX]

            title_text = title_td.css('::text').get().strip()

            self._td_map[title_text] = data_td

    def get_cell(self, top, left) -> scrapy.Selector:
        assert top is None
        try:
            return self._td_map[left]
        except KeyError as err:
            raise HeaderMismatchError(repr(err))

    def has_header(self, top=None, left=None) -> bool:
        return (top is None) and (left in self._td_map)


