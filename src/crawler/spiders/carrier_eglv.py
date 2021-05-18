import base64
from typing import Dict, List

import requests
import scrapy

from crawler.core_carrier.base import CARRIER_RESULT_STATUS_FATAL
from crawler.core_carrier.base_spiders import (
    BaseCarrierSpider,
    CARRIER_DEFAULT_SETTINGS,
    DISABLE_DUPLICATE_REQUEST_FILTER,
)
from crawler.core_carrier.exceptions import (
    CarrierResponseFormatError,
    CarrierInvalidMblNoError,
    BaseCarrierError,
    SuspiciousOperationError,
)
from crawler.core_carrier.items import (
    ContainerStatusItem,
    LocationItem,
    ContainerItem,
    MblItem,
    BaseCarrierItem,
    ExportErrorData,
    DebugItem,
)
from crawler.core_carrier.request_helpers import RequestOption
from crawler.core_carrier.rules import RuleManager, BaseRoutingRule
from crawler.extractors.selector_finder import (
    find_selector_from,
    CssQueryExistMatchRule,
    CssQueryTextStartswithMatchRule,
)
from crawler.extractors.table_cell_extractors import FirstTextTdExtractor
from crawler.extractors.table_extractors import BaseTableLocator, HeaderMismatchError, TableExtractor

CAPTCHA_RETRY_LIMIT = 3
EGLV_INFO_URL = 'https://www.shipmentlink.com/servlet/TDB1_CargoTracking.do'
EGLV_CAPTCHA_URL = 'https://www.shipmentlink.com/servlet/TUF1_CaptchaUtils'


class CarrierEglvSpider(BaseCarrierSpider):
    name = 'carrier_eglv'

    custom_settings = {
        **CARRIER_DEFAULT_SETTINGS,
        **DISABLE_DUPLICATE_REQUEST_FILTER,
    }

    def __init__(self, *args, **kwargs):
        super(CarrierEglvSpider, self).__init__(*args, **kwargs)

        rules = [
            CaptchaRoutingRule(),
            MainInfoRoutingRule(),
            FilingStatusRoutingRule(),
            ReleaseStatusRoutingRule(),
            ContainerStatusRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)

    def start(self):
        option = CaptchaRoutingRule.build_request_option(mbl_no=self.mbl_no)
        yield self._build_request_by(option=option)

    def parse(self, response):
        yield DebugItem(info={'meta': dict(response.meta)})

        routing_rule = self._rule_manager.get_rule_by_response(response=response)

        if routing_rule.name != 'CAPTCHA':
            save_name = routing_rule.get_save_name(response=response)
            self._saver.save(to=save_name, text=response.text)

        for result in routing_rule.handle(response=response):
            if isinstance(result, BaseCarrierItem):
                yield result
            elif isinstance(result, RequestOption):
                yield self._build_request_by(option=result)
            else:
                raise RuntimeError()

    def _build_request_by(self, option: RequestOption):
        meta = {
            RuleManager.META_CARRIER_CORE_RULE_NAME: option.rule_name,
            **option.meta,
        }

        if option.method == RequestOption.METHOD_GET:
            return scrapy.Request(
                url=option.url,
                meta=meta,
            )
        elif option.method == RequestOption.METHOD_POST_FORM:
            return scrapy.FormRequest(
                url=option.url,
                formdata=option.form_data,
                meta=meta,
            )
        else:
            raise SuspiciousOperationError(msg=f'Unexpected request method: `{option.method}`')


# -------------------------------------------------------------------------------


class CaptchaRoutingRule(BaseRoutingRule):
    name = 'CAPTCHA'

    def __init__(self):
        self._captcha_analyzer = CaptchaAnalyzer()

    @classmethod
    def build_request_option(cls, mbl_no: str) -> RequestOption:
        return RequestOption(
            method=RequestOption.METHOD_GET,
            rule_name=cls.name,
            url=EGLV_CAPTCHA_URL,
            meta={'mbl_no': mbl_no},
        )

    def get_save_name(self, response) -> str:
        return ''  # ignore captcha

    def handle(self, response):
        mbl_no = response.meta['mbl_no']

        captcha_base64 = base64.b64encode(response.body)
        verification_code = self._captcha_analyzer.analyze_captcha(captcha_base64=captcha_base64)

        yield MainInfoRoutingRule.build_request_option(mbl_no=mbl_no, verification_code=verification_code)


# -------------------------------------------------------------------------------


class CarrierCaptchaMaxRetryError(BaseCarrierError):
    status = CARRIER_RESULT_STATUS_FATAL

    def build_error_data(self):
        return ExportErrorData(status=self.status, detail='<captcha-max-retry-error>')


class MainInfoRoutingRule(BaseRoutingRule):
    name = 'MAIN_INFO'

    def __init__(self):
        self._retry_count = 0

    @classmethod
    def build_request_option(cls, mbl_no: str, verification_code: str) -> RequestOption:
        form_data = {
            'BL': mbl_no,
            'CNTR': '',
            'bkno': '',
            'TYPE': 'BL',
            'NO': [mbl_no, '', '', '', '', ''],
            'SEL': 's_bl',
            'captcha_input': verification_code,
            'hd_captcha_input': '',
        }

        return RequestOption(
            method=RequestOption.METHOD_POST_FORM,
            rule_name=cls.name,
            url=EGLV_INFO_URL,
            form_data=form_data,
            meta={'mbl_no': mbl_no},
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.html'

    def handle(self, response):
        mbl_no = response.meta['mbl_no']

        if self._check_captcha(response=response):
            for item in self._handle_main_info_page(response=response, mbl_no=mbl_no):
                yield item

        elif self._retry_count < CAPTCHA_RETRY_LIMIT:
            self._retry_count += 1
            yield CaptchaRoutingRule.build_request_option(mbl_no=mbl_no)

        else:
            raise CarrierCaptchaMaxRetryError()

    @staticmethod
    def _check_captcha(response) -> bool:
        # wrong captcha -> back to search page
        message_under_search_table = ' '.join(
            response.css('table table[cellpadding="1"] tr td.f12rown1::text').getall()
        )
        if isinstance(message_under_search_table, str):
            message_under_search_table = message_under_search_table.strip()
        back_to_search_page_message = 'Shipments tracing by Booking NO. is available for specific countries/areas only.'

        if message_under_search_table == back_to_search_page_message:
            return False
        else:
            return True

    def _handle_main_info_page(self, response, mbl_no):
        self._check_mbl_no(response=response)

        mbl_no_info = self._extract_hidden_info(response=response)
        basic_info = self._extract_basic_info(response=response)
        vessel_info = self._extract_vessel_info(response=response, pod=basic_info['pod_name'])

        yield MblItem(
            mbl_no=mbl_no_info['mbl_no'],
            vessel=vessel_info['vessel'],
            voyage=vessel_info['voyage'],
            por=LocationItem(name=basic_info['por_name']),
            pol=LocationItem(name=basic_info['pol_name']),
            pod=LocationItem(name=basic_info['pod_name']),
            final_dest=LocationItem(name=basic_info['dest_name']),
            place_of_deliv=LocationItem(name=basic_info['place_of_deliv_name']),
            etd=basic_info['etd'],
            eta=vessel_info['eta'],
            cargo_cutoff_date=basic_info['cargo_cutoff_date'],
        )

        container_list = self._extract_container_info(response=response)
        for container in container_list:
            yield ContainerItem(
                container_key=container['container_no'],
                container_no=container['container_no'],
            )

            yield ContainerStatusRoutingRule.build_request_option(
                mbl_no=mbl_no,
                container_no=container['container_no'],
                onboard_date=mbl_no_info['onboard_date'],
                pol=mbl_no_info['pol_code'],
                pod=mbl_no_info['pod_code'],
                podctry=mbl_no_info['podctry'],
            )

        if self._check_filing_status(response=response):
            first_container_no = self._get_first_container_no(container_list=container_list)
            yield FilingStatusRoutingRule.build_request_option(
                mbl_no=mbl_no,
                pod=mbl_no_info['pod_code'],
                first_container_no=first_container_no,
            )

        yield ReleaseStatusRoutingRule.build_request_option(mbl_no=mbl_no)

    @staticmethod
    def _check_mbl_no(response):
        script_text = response.css('script::text').get()
        if 'B/L No. is not valid, please check again, thank you.' in script_text:
            raise CarrierInvalidMblNoError()

        message_under_search_table = response.css('table table tr td.f12wrdb1::text').get()
        if isinstance(message_under_search_table, str):
            message_under_search_table = message_under_search_table.strip()
        mbl_invalid_message = (
            'No information on B/L No., please enter a valid B/L No. or contact our offices for assistance.'
        )

        if message_under_search_table == mbl_invalid_message:
            raise CarrierInvalidMblNoError()

    @staticmethod
    def _extract_hidden_info(response: scrapy.Selector) -> Dict:
        tables = response.css('table table')

        hidden_form_query = 'form[name=frmCntrMove]'
        rule = CssQueryExistMatchRule(css_query=hidden_form_query)
        table_selector = find_selector_from(selectors=tables, rule=rule)
        if table_selector is None:
            raise CarrierResponseFormatError(reason='Can not found Basic Information table!!!')

        return {
            'mbl_no': table_selector.css('input[name=bl_no]::attr(value)').get(),
            'pol_code': table_selector.css('input[name=pol]::attr(value)').get(),
            'pod_code': table_selector.css('input[name=pod]::attr(value)').get(),
            'onboard_date': table_selector.css('input[name=onboard_date]::attr(value)').get(),
            'podctry': table_selector.css('input[name=podctry]::attr(value)').get(),
        }

    @staticmethod
    def _extract_basic_info(response: scrapy.Selector) -> Dict:
        tables = response.css('table table')

        rule = CssQueryTextStartswithMatchRule(css_query='td.f13tabb2::text', startswith='Basic Information')
        table_selector = find_selector_from(selectors=tables, rule=rule)
        if table_selector is None:
            raise CarrierResponseFormatError(reason='Can not found Basic Information table!!!')

        left_table_locator = LeftBasicInfoTableLocator()
        left_table_locator.parse(table=table_selector)
        left_table = TableExtractor(table_locator=left_table_locator)

        right_table_locator = RightBasicInfoTableLocator()
        right_table_locator.parse(table=table_selector)
        right_table = TableExtractor(table_locator=right_table_locator)

        return {
            'por_name': left_table.extract_cell(None, 'Place of Receipt') or None,
            'pol_name': left_table.extract_cell(None, 'Port of Loading') or None,
            'pod_name': left_table.extract_cell(None, 'Port of Discharge') or None,
            'dest_name': left_table.extract_cell(None, 'OCP Final Destination') or None,
            'place_of_deliv_name': left_table.extract_cell(None, 'Place of Delivery') or None,
            'etd': right_table.extract_cell(None, 'Estimated On Board Date') or None,
            'cargo_cutoff_date': right_table.extract_cell(None, 'Cut Off Date') or None,
        }

    def _extract_vessel_info(self, response: scrapy.Selector, pod: str) -> Dict:
        tables = response.css('table table')

        rule = CssQueryTextStartswithMatchRule(css_query='td.f13tabb2::text', startswith='Plan Moves')
        table_selector = find_selector_from(selectors=tables, rule=rule)
        if table_selector is None:
            return {
                'eta': None,
                'vessel': None,
                'voyage': None,
            }

        table_locator = NameOnTopHeaderTableLocator()
        table_locator.parse(table=table_selector)
        table = TableExtractor(table_locator=table_locator)

        for left in table_locator.iter_left_headers():
            if table.extract_cell('Location', left) == pod:
                vessel_voyage = table.extract_cell('Estimated Arrival Vessel/Voyage', left)
                vessel, voyage = self._get_vessel_voyage(vessel_voyage=vessel_voyage)
                return {
                    'eta': table.extract_cell('Estimated Arrival Date', left),
                    'vessel': vessel,
                    'voyage': voyage,
                }

        return {
            'eta': None,
            'vessel': None,
            'voyage': None,
        }

    @staticmethod
    def _get_vessel_voyage(vessel_voyage: str):
        if vessel_voyage == 'To be Advised':
            return '', ''

        vessel, voyage = vessel_voyage.rsplit(sep=' ', maxsplit=1)
        return vessel, voyage

    @staticmethod
    def _extract_container_info(response: scrapy.Selector) -> List:
        tables = response.css('table table')

        rule = CssQueryTextStartswithMatchRule(
            css_query='td.f13tabb2::text',
            startswith='Container(s) information on B/L and Current Status',
        )
        table_selector = find_selector_from(selectors=tables, rule=rule)
        if table_selector is None:
            return []

        table_locator = NameOnTopHeaderTableLocator()
        table_locator.parse(table=table_selector)
        table = TableExtractor(table_locator=table_locator)

        return_list = []

        for left in table_locator.iter_left_headers():
            return_list.append(
                {
                    'container_no': table.extract_cell('Container No.', left, FirstTextTdExtractor('a::text')),
                    'date': table.extract_cell('Date', left),
                }
            )

        return return_list

    @staticmethod
    def _check_filing_status(response: scrapy.Selector):
        tables = response.css('table')

        rule = CssQueryTextStartswithMatchRule(css_query='td a::text', startswith='Customs Information')
        return bool(find_selector_from(selectors=tables, rule=rule))

    @staticmethod
    def _get_first_container_no(container_list: List):
        return container_list[0]['container_no']


class LeftBasicInfoTableLocator(BaseTableLocator):
    """
    +-----------------------------------+ <tbody>
    | Basic Information ...             | <tr>
    +---------+---------+-----+---------+
    | Title 1 | Data 1  |     |         | <tr>
    +---------+---------+-----+---------+
    | Title 2 | Data 2  |     |         | <tr>
    +---------+---------+-----+---------+
    | Title 3 | Data 3  |     |         | <tr>
    +---------+---------+-----+---------+
    | ...     |         |     |         | <tr>
    +---------+---------+-----+---------+
    | Title N | Data N  |     |         | <tr>
    +---------+---------+-----+---------+ </tbody>
    """

    TR_CONTENT_BEGIN_INDEX = 1
    TD_TITLE_INDEX = 0
    TD_DATA_INDEX = 1

    def __init__(self):
        self._td_map = {}  # title: data

    def parse(self, table: scrapy.Selector):
        content_tr_list = table.css('tr')[self.TR_CONTENT_BEGIN_INDEX :]

        for content_tr in content_tr_list:
            title_td = content_tr.css('td')[self.TD_TITLE_INDEX]
            data_td = content_tr.css('td')[self.TD_DATA_INDEX]

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


class RightBasicInfoTableLocator(BaseTableLocator):
    """
    +-----------------------------------+ <tbody>
    | Basic Information ...             | <tr>
    +-----+---------+---------+---------+
    |     |         | Title 1 | Data 1  | <tr>
    +-----+---------+---------+---------+
    |     |         | Title 2 | Data 2  | <tr>
    +-----+---------+---------+---------+
    |     |         | Title 3 | Data 3  | <tr>
    +-----+---------+---------+---------+
    |     |         | ...     | ...     | <tr>
    +-----+---------+---------+---------+
    |     |         | Title N | Data N  | <tr>
    +-----+---------+---------+---------+ </tbody>
    """

    TR_CONTENT_BEGIN_INDEX = 1
    TD_TITLE_INDEX = 2
    TD_DATA_INDEX = 3

    def __init__(self):
        self._td_map = {}  # title: data

    def parse(self, table: scrapy.Selector):
        content_tr_list = table.css('tr')[self.TR_CONTENT_BEGIN_INDEX :]

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


# -------------------------------------------------------------------------------


class FilingStatusRoutingRule(BaseRoutingRule):
    name = 'FILING_STATUS'

    @classmethod
    def build_request_option(cls, mbl_no: str, first_container_no: str, pod: str) -> RequestOption:
        form_data = {
            'TYPE': 'GetDispInfo',
            'Item': 'AMSACK',
            'BL': mbl_no,
            'firstCtnNo': first_container_no,
            'pod': pod,
        }

        return RequestOption(
            method=RequestOption.METHOD_POST_FORM,
            rule_name=cls.name,
            url=EGLV_INFO_URL,
            form_data=form_data,
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.html'

    def handle(self, response):
        status = self._extract_filing_status(response=response)

        yield MblItem(
            us_filing_status=status['filing_status'],
            us_filing_date=status['filing_date'],
        )

    @staticmethod
    def _extract_filing_status(response: scrapy.Selector) -> Dict:
        table_selector = response.css('table')

        if table_selector is None:
            return {
                'filing_status': None,
                'filing_date': None,
            }

        table_locator = NameOnTopHeaderTableLocator()
        table_locator.parse(table=table_selector)
        table = TableExtractor(table_locator=table_locator)

        for left in table_locator.iter_left_headers():
            if table.extract_cell('Customs', left) == 'US':
                return {
                    'filing_status': table.extract_cell('Description', left, FirstTextTdExtractor('a::text')),
                    'filing_date': table.extract_cell('Date', left),
                }

        return {
            'filing_status': None,
            'filing_date': None,
        }


# -------------------------------------------------------------------------------


class ReleaseStatusRoutingRule(BaseRoutingRule):
    name = 'RELEASE_STATUS'

    @classmethod
    def build_request_option(cls, mbl_no: str) -> RequestOption:
        form_data = {
            'TYPE': 'GetDispInfo',
            'Item': 'RlsStatus',
            'BL': mbl_no,
        }

        return RequestOption(
            method=RequestOption.METHOD_POST_FORM, rule_name=cls.name, url=EGLV_INFO_URL, form_data=form_data
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.html'

    def handle(self, response):
        release_status = self._extract_release_status(response=response)

        yield MblItem(
            carrier_status=release_status['carrier_status'],
            carrier_release_date=release_status['carrier_release_date'],
            us_customs_status=release_status['us_customs_status'],
            us_customs_date=release_status['us_customs_date'],
            customs_release_status=release_status['customs_release_status'],
            customs_release_date=release_status['customs_release_date'],
        )

    @staticmethod
    def _extract_release_status(response: scrapy.Selector) -> Dict:
        table_selector = response.css('table')

        if not table_selector:
            return {
                'carrier_status': None,
                'carrier_release_date': None,
                'us_customs_status': None,
                'us_customs_date': None,
                'customs_release_status': None,
                'customs_release_date': None,
            }

        first_message = table_selector.css('tr td::text').get()
        if first_message.strip() == 'Data not found.':
            return {
                'carrier_status': None,
                'carrier_release_date': None,
                'us_customs_status': None,
                'us_customs_date': None,
                'customs_release_status': None,
                'customs_release_date': None,
            }

        carrier_status_table_locator = CarrierStatusTableLocator()
        carrier_status_table_locator.parse(table=table_selector)
        carrier_status_table = TableExtractor(table_locator=carrier_status_table_locator)

        us_customs_status_table_locator = USCustomStatusTableLocator()
        us_customs_status_table_locator.parse(table=table_selector)
        us_customs_status_table = TableExtractor(table_locator=us_customs_status_table_locator)

        custom_release_status_table_locator = CustomReleaseStatusTableLocator()
        custom_release_status_table_locator.parse(table=table_selector)
        custom_release_status_table = TableExtractor(table_locator=custom_release_status_table_locator)

        return {
            'carrier_status': carrier_status_table.extract_cell(top='Status', left=None) or None,
            'carrier_release_date': carrier_status_table.extract_cell(top='Carrier Date', left=None) or None,
            'us_customs_status': us_customs_status_table.extract_cell(top='I.T. NO.', left=None) or None,
            'us_customs_date': us_customs_status_table.extract_cell(top='Date', left=None) or None,
            'customs_release_status': custom_release_status_table.extract_cell(top='Status', left=None) or None,
            'customs_release_date': custom_release_status_table.extract_cell(top='Date', left=None) or None,
        }


class CarrierStatusTableLocator(BaseTableLocator):
    """
    +---------------------------------------------------------------+ <tbody>
    | Release Status                                                | <tr>
    +---------+----------+---------+---------+-----------+----------+
    | Carrier | Title 1  | Title 2 | Title 3 |  Title 4  | Title 5  | <tr>
    |         +----------+---------+---------+-----------+----------+
    | Status  | Data 1   | Data 2  | Data 3  |  Data 4   | Data 5   | <tr>
    +---------+----------+---------+---------+-----------+----------+
    |         |          |                   |           |          | <tr>
    |         +----------+-------------------+-----------+----------+
    |         |          |                   |           |          | <tr>
    |         +----------+-------------------+-----------+----------+
    |         |          |                               |          | <tr>
    |         +----------+-------------------------------+----------+
    |         |          |                               |          | <tr>
    +---------+----------+-------------------------------+----------+ </tbody>
    """

    TR_TITLE_INDEX = 1
    TR_DATA_INDEX = 2

    def __init__(self):
        self._td_map = {}  # title: data

        self._title_remap = {  # title_index: rename title
            3: 'Carrier Date',
            5: 'Way Bill Date',
        }

    def parse(self, table: scrapy.Selector):
        title_tr = table.css('tr')[self.TR_TITLE_INDEX]
        data_tr = table.css('tr')[self.TR_DATA_INDEX]

        title_text_list = title_tr.css('td::text').getall()
        data_td_list = data_tr.css('td')

        for data_index, data_td in enumerate(data_td_list):
            title_index = data_index + 1  # index shift by row span
            title_text = title_text_list[title_index].strip()

            new_title_text = self._title_remap.get(title_index, title_text)

            self._td_map[new_title_text] = data_td

    def get_cell(self, top, left) -> scrapy.Selector:
        assert left is None
        try:
            return self._td_map[top]
        except KeyError as err:
            raise HeaderMismatchError(repr(err))

    def has_header(self, top=None, left=None) -> bool:
        return (top in self._td_map) and (left is None)


class USCustomStatusTableLocator(BaseTableLocator):
    """
    +----------------------------------------------------------------+ <tbody>
    | Release Status                                                 | <tr>
    +---------+----------+---------+---------+------------+----------+
    |         |          |         |         |            |          | <tr>
    +         +----------+---------+---------+------------+----------+
    |         |          |         |         |            |          | <tr>
    +---------+----------+---------+---------+------------+----------+
    | Customs | Title 1  |     Title 2       |  Title 3   | Title 4  | <tr>
    |         +----------+-------------------+------------+----------+
    |         | Data 1   |     Data 2        |  Data 3    | Data 4   | <tr>
    |         +----------+-------------------+------------+----------+
    | Status  |          |                                |          | <tr>
    |         +----------+--------------------------------+----------+
    |         |          |                                |          | <tr>
    +---------+----------+--------------------------------+----------+ </tbody>
    """

    TR_TITLE_INDEX = 3
    TR_DATA_INDEX = 4

    def __init__(self):
        self._td_map = {}  # title: data

    def parse(self, table: scrapy.Selector):
        title_tr = table.css('tr')[self.TR_TITLE_INDEX]
        data_tr = table.css('tr')[self.TR_DATA_INDEX]

        title_text_list = title_tr.css('td::text').getall()
        data_td_list = data_tr.css('td')

        for data_index, data_td in enumerate(data_td_list):
            title_index = data_index + 1  # index shift by row span

            title_text = title_text_list[title_index].strip()

            self._td_map[title_text] = data_td

    def get_cell(self, top, left) -> scrapy.Selector:
        assert left is None
        try:
            return self._td_map[top]
        except KeyError as err:
            raise HeaderMismatchError(repr(err))

    def has_header(self, top=None, left=None) -> bool:
        return (top in self._td_map) and (left is None)


class CustomReleaseStatusTableLocator(BaseTableLocator):
    """
    +----------------------------------------------------------------+ <tbody>
    | Release Status                                                 | <tr>
    +---------+----------+---------+---------+------------+----------+
    |         |          |         |         |            |          | <tr>
    |         +----------+---------+---------+------------+----------+
    |         |          |         |         |            |          | <tr>
    +---------+----------+---------+---------+------------+----------+
    | Customs |          |                   |            |          | <tr>
    |         +----------+-------------------+------------+----------+
    |         |          |                   |            |          | <tr>
    |         +----------+-------------------+------------+----------+
    | Status  | Title 1  |             Title 2            | Title 3  | <tr>
    |         +----------+--------------------------------+----------+
    |         | Data 1   |             Data 2             | Data 3   | <tr>
    +---------+----------+--------------------------------+----------+ </tbody>
    """

    TR_TITLE_INDEX = 5
    TR_DATA_INDEX = 6

    def __init__(self):
        self._td_map = {}  # title: data

    def parse(self, table: scrapy.Selector):
        title_tr = table.css('tr')[self.TR_TITLE_INDEX]
        data_tr = table.css('tr')[self.TR_DATA_INDEX]

        title_text_list = title_tr.css('td::text').getall()
        data_td_list = data_tr.css('td')

        for data_index, data_td in enumerate(data_td_list):
            title_index = data_index

            title_text = title_text_list[title_index].strip()

            self._td_map[title_text] = data_td

    def get_cell(self, top, left) -> scrapy.Selector:
        assert left is None
        try:
            return self._td_map[top]
        except KeyError as err:
            raise HeaderMismatchError(repr(err))

    def has_header(self, top=None, left=None) -> bool:
        return (top in self._td_map) and (left is None)


# -------------------------------------------------------------------------------


class ContainerStatusRoutingRule(BaseRoutingRule):
    name = 'CONTAINER_STATUS'

    @classmethod
    def build_request_option(
        cls, mbl_no: str, container_no: str, onboard_date: str, pol: str, pod: str, podctry: str
    ) -> RequestOption:
        form_data = {
            'bl_no': mbl_no,
            'cntr_no': container_no,
            'onboard_date': onboard_date,
            'pol': pol,
            'pod': pod,
            'podctry': podctry,
            'TYPE': 'CntrMove',
        }

        return RequestOption(
            method=RequestOption.METHOD_POST_FORM,
            rule_name=cls.name,
            url=EGLV_INFO_URL,
            form_data=form_data,
            meta={'container_no': container_no},
        )

    def get_save_name(self, response) -> str:
        container_no = response.meta['container_no']
        return f'{self.name}_{container_no}.html'

    def handle(self, response):
        container_no = response.meta['container_no']

        container_status_list = self._extract_container_status_list(response=response)
        for container_status in container_status_list:
            yield ContainerStatusItem(
                container_key=container_no,
                description=container_status['description'],
                local_date_time=container_status['timestamp'],
                location=LocationItem(name=container_status['location_name']),
            )

    @staticmethod
    def _extract_container_status_list(response: scrapy.Selector) -> List[Dict]:
        tables = response.css('table table')

        rule = CssQueryTextStartswithMatchRule(css_query='td.f13tabb2::text', startswith='Container Moves')
        table_selector = find_selector_from(selectors=tables, rule=rule)
        if table_selector is None:
            raise CarrierResponseFormatError(reason='Can not found Container Status table!!!')

        table_locator = NameOnTopHeaderTableLocator()
        table_locator.parse(table=table_selector)
        table = TableExtractor(table_locator=table_locator)

        container_status_list = []
        for left in table_locator.iter_left_headers():
            container_status_list.append(
                {
                    'timestamp': table.extract_cell('Date', left),
                    'description': table.extract_cell('Container Moves', left),
                    'location_name': table.extract_cell('Location', left),
                }
            )

        return container_status_list


# -------------------------------------------------------------------------------


class NameOnTopHeaderTableLocator(BaseTableLocator):
    """
    +-----------------------------------+ <tbody>
    | Table Name                        | <tr>
    +---------+---------+-----+---------+
    | Title 1 | Title 2 | ... | Title N | <tr>
    +---------+---------+-----+---------+
    | Data    |         |     |         | <tr>
    +---------+---------+-----+---------+
    | Data    |         |     |         | <tr>
    +---------+---------+-----+---------+
    | ...     |         |     |         | <tr>
    +---------+---------+-----+---------+
    | Data    |         |     |         | <tr>
    +---------+---------+-----+---------+ </tbody>
    """

    TR_TITLE_INDEX = 1
    TR_DATA_BEGIN_INDEX = 2

    def __init__(self):
        self._td_map = {}  # title: [data, ...]
        self._data_len = 0

    def parse(self, table: scrapy.Selector):
        title_tr = table.css('tr')[self.TR_TITLE_INDEX]
        data_tr_list = table.css('tr')[self.TR_DATA_BEGIN_INDEX :]

        title_text_list = title_tr.css('td::text').getall()

        for title_index, title_text in enumerate(title_text_list):
            data_index = title_index

            title_text = title_text.strip()
            self._td_map[title_text] = []

            for data_tr in data_tr_list:
                data_td = data_tr.css('td')[data_index]

                self._td_map[title_text].append(data_td)

        first_title_text = title_text_list[0]
        self._data_len = len(self._td_map[first_title_text])

    def get_cell(self, top, left) -> scrapy.Selector:
        try:
            return self._td_map[top][left]
        except KeyError as err:
            raise HeaderMismatchError(repr(err))

    def has_header(self, top=None, left=None) -> bool:
        return (top in self._td_map) and (left is None)

    def iter_left_headers(self):
        for index in range(self._data_len):
            yield index


# -------------------------------------------------------------------------------


class CaptchaAnalyzer:

    SERVICE_URL = 'https://nymnwfny58.execute-api.us-west-2.amazonaws.com/dev/captcha-eglv'
    headers = {
        'x-api-key': 'jzeitRn28t5UMxRA31Co46PfseW9hTK43DLrBtb6',
    }

    def analyze_captcha(self, captcha_base64: bytes) -> str:
        req = requests.post(url=self.SERVICE_URL, data=captcha_base64, headers=self.headers)
        return req.content
