import abc
import re
from typing import List, Dict

import scrapy
from scrapy import Selector

from crawler.core_carrier.base_spiders import BaseCarrierSpider
from crawler.core_carrier.rules import RuleManager, RoutingRequest, BaseRoutingRule
from crawler.core_carrier.items import (
    BaseCarrierItem, LocationItem, VesselItem, ContainerItem, ContainerStatusItem)
from crawler.core_carrier.exceptions import CarrierResponseFormatError, CarrierInvalidMblNoError
from crawler.extractors.table_extractors import BaseTableLocator, HeaderMismatchError, TableExtractor

WHLC_BASE_URL = 'https://www.wanhai.com/views'


class CarrierWhlcSpider(BaseCarrierSpider):
    name = 'carrier_whlc'

    def __init__(self, *args, **kwargs):
        super(CarrierWhlcSpider, self).__init__(*args, **kwargs)

        rules = [
            ListRoutingRule(),
            DetailRoutingRule(),
            HistoryRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)

    def start_requests(self):
        routing_request = ListRoutingRule.build_routing_request(mbl_no=self.mbl_no, cookies={}, view_state='')
        yield self._rule_manager.build_request_by(routing_request=routing_request)

    def parse(self, response):
        routing_rule = self._rule_manager.get_rule_by_response(response=response)

        for result in routing_rule.handle(response=response):
            if isinstance(result, BaseCarrierItem):
                yield result
            elif isinstance(result, RoutingRequest):
                yield self._rule_manager.build_request_by(routing_request=result)
            else:
                raise RuntimeError()


# -------------------------------------------------------------------------------

class ListRoutingRule(BaseRoutingRule):
    name = 'LIST'

    JDT_DETAIL = 'j_idt36:0:j_idt40'
    JDT_HISTORY = 'j_idt36:0:j_idt83'

    @classmethod
    def build_routing_request(cls, mbl_no: str, cookies, view_state) -> RoutingRequest:
        form_data = {
            'cargoTrackListBean': 'cargoTrackListBean',
            'cargoType': '2',
            'q_ref_no1': mbl_no,
            'j_idt6': 'Query',
            'javax.faces.ViewState': view_state,
        }
        request = scrapy.FormRequest(
            url=f'{WHLC_BASE_URL}/quick/cargo_tracking.xhtml',
            method='POST',
            cookies=cookies,
            formdata=form_data,
            meta={'mbl_no': mbl_no, 'cookies': cookies},
        )
        return RoutingRequest(request=request, rule_name=cls.name)

    def handle(self, response):
        mbl_no = response.meta['mbl_no']
        cookies = response.meta['cookies']
        view_state = self._extract_view_state(response=response)
        if cookies == {}:
            for cookie in response.headers.getlist('Set-Cookie'):
                key_value_list = cookie.decode("utf-8").split(';')[0].split('=')
                cookies[key_value_list[0]] = key_value_list[1]

            yield ListRoutingRule.build_routing_request(mbl_no, cookies, view_state)
        else:
            self.check_response(response)

            container_list = self._extract_container_info(response=response)
            for container in container_list:
                container_no = container['container_no']

                yield ContainerItem(
                    container_key=container_no,
                    container_no=container_no,
                )

                yield DetailRoutingRule.build_routing_request(
                    mbl_no, container_no, view_state, self.JDT_DETAIL, cookies)

                yield HistoryRoutingRule.build_routing_request(
                    mbl_no, container_no, view_state, self.JDT_HISTORY, cookies)

    @staticmethod
    def check_response(response):
        if response.css('form[action="/views/AlertMsgPage.xhtml"]'):
            raise CarrierInvalidMblNoError()

    @staticmethod
    def _extract_view_state(response: scrapy.Selector) -> str:
        return response.css('input[name="javax.faces.ViewState"]::attr(value)').get()

    @staticmethod
    def _extract_container_info(response: scrapy.Selector) -> List:
        pattern = re.compile(r'^(?P<container_no>\w+)')

        table_selector = response.css('table.tbl-list')[0]
        table_locator = ContainerListTableLocator()
        table_locator.parse(table=table_selector)
        table = TableExtractor(table_locator=table_locator)

        return_list = []
        for left in table_locator.iter_left_headers():
            container_no_text = table.extract_cell('Ctnr No.', left)
            m = pattern.match(container_no_text)
            if not m:
                raise CarrierResponseFormatError(reason='container_no not match')
            container_no = m.group('container_no')

            return_list.append({
                'container_no': container_no,
            })

        return return_list


class ContainerListTableLocator(BaseTableLocator):

    TR_TITLE_INDEX = 0
    TR_DATA_BEGIN_INDEX = 1

    def __init__(self):
        self._td_map = {}
        self._data_len = 0

    def parse(self, table: Selector):
        title_tr = table.css('tr')[self.TR_TITLE_INDEX]
        data_tr_list = table.css('tr')[self.TR_DATA_BEGIN_INDEX:]

        title_text_list = title_tr.css('th::text').getall()

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

class DetailRoutingRule(BaseRoutingRule):
    name = 'DETAIL'

    @classmethod
    def build_routing_request(cls, mbl_no: str, container_no, view_state, jdt, cookies) -> RoutingRequest:
        form_data = {
            'cargoTrackListBean': 'cargoTrackListBean',
            'javax.faces.ViewState': view_state,
            jdt: jdt,
            'q_bl_no': mbl_no,
            'q_ctnr_no': container_no,
        }
        request = scrapy.FormRequest(
            url=f'{WHLC_BASE_URL}/cargoTrack/CargoTrackList.xhtml',
            method='POST',
            cookies=cookies,
            formdata=form_data,
            meta={
                'mbl_no': mbl_no,
                'cookies': cookies,
            },
        )
        return RoutingRequest(request=request, rule_name=cls.name)

    def handle(self, response):
        date_information = self._extract_date_information(response=response)
        yield VesselItem(
            pol=LocationItem(un_lo_code=date_information['pol_un_lo_code']),
            vessel=date_information['pol_vessel'],
            voyage=date_information['pol_voyage'],
            etd=date_information['pol_etd'],
        )

        yield VesselItem(
            pod=LocationItem(un_lo_code=date_information['pod_un_lo_code']),
            vessel=date_information['pod_vessel'],
            voyage=date_information['pod_voyage'],
            eta=date_information['pod_eta'],
        )

    @staticmethod
    def _extract_date_information(response) -> Dict:
        pattern = re.compile(r'^(?P<vessel>[^/]+) / (?P<voyage>[^/]+)$')

        match_rule = NameOnTableMatchRule(name='2. Departure Date / Arrival Date Information')
        table_selector = find_selector_from(selectors=response.css('table.tbl-list'), rule=match_rule)

        if table_selector is None:
            raise CarrierResponseFormatError(reason='data information table not found')

        location_table_locator = LocationLeftTableLocator()
        location_table_locator.parse(table=table_selector)
        location_table = TableExtractor(table_locator=location_table_locator)

        date_table_locator = DateLeftTableLocator()
        date_table_locator.parse(table=table_selector)
        date_table = TableExtractor(table_locator=date_table_locator)

        un_lo_code_index = 0
        vessel_voyage_index = 1
        date_index = 0

        pol_vessel_voyage = location_table.extract_cell(top=vessel_voyage_index, left='Loading Port')
        pol_m = pattern.match(pol_vessel_voyage)
        pol_vessel = pol_m.group('vessel')
        pol_voyage = pol_m.group('voyage')

        pod_vessel_voyage = location_table.extract_cell(top=vessel_voyage_index, left='Discharging Port')
        pod_m = pattern.match(pod_vessel_voyage)
        pod_vessel = pod_m.group('vessel')
        pod_voyage = pod_m.group('voyage')

        return {
            'pol_un_lo_code': location_table.extract_cell(top=un_lo_code_index, left='Loading Port'),
            'pod_un_lo_code': location_table.extract_cell(top=un_lo_code_index, left='Discharging Port'),
            'pol_vessel': pol_vessel,
            'pol_voyage': pol_voyage,
            'pod_vessel': pod_vessel,
            'pod_voyage': pod_voyage,
            'pol_etd': date_table.extract_cell(top=date_index, left='Arrival Date'),
            'pod_eta': date_table.extract_cell(top=date_index, left='Departure Date'),
        }


class LocationLeftTableLocator(BaseTableLocator):
    """
        +------------------------------------------------+ <tbody>
        | Title 1 | Data 1  | Data 2 | Title    | Data   | <tr>
        +---------+---------+--------+----------+--------+
        | Title 2 |         |        | Title    | Data   | <tr>
        +---------+---------+--------+----------+--------+ </tbody>
        (       only use here        )
    """

    TR_TITLE_INDEX_BEGIN = 1
    TH_TITLE_INDEX = 0
    TD_DATA_INDEX_BEGIN = 0
    TD_DATA_INDEX_END = 2

    def __init__(self):
        self._td_map = {}
        self._left_header_set = set()

    def parse(self, table: Selector):
        top_index_set = set()
        tr_list = table.css('tr')[self.TR_TITLE_INDEX_BEGIN:]

        for tr in tr_list:
            left_header = tr.css('th::text')[self.TH_TITLE_INDEX].get().strip()
            self._left_header_set.add(left_header)

            data_td_list = tr.css('td')[self.TD_DATA_INDEX_BEGIN:self.TD_DATA_INDEX_END]
            for top_index, td in enumerate(data_td_list):
                top_index_set.add(top_index)
                td_dict = self._td_map.setdefault(top_index, {})
                td_dict[left_header] = td

    def get_cell(self, top, left) -> Selector:
        try:
            return self._td_map[top][left]
        except KeyError as err:
            raise HeaderMismatchError(repr(err))

    def has_header(self, top=None, left=None) -> bool:
        return (top is None) and (left in self._left_header_set)


class DateLeftTableLocator(BaseTableLocator):
    """
        +------------------------------------------------+ <tbody>
        | Title   | Data    | Data   | Title 1  | Data   | <tr>
        +---------+---------+--------+----------+--------+
        | Title   |         |        | Title 2  | Data   | <tr>
        +---------+---------+--------+----------+--------+ </tbody>
                                     (   only use here   )
    """

    TR_TITLE_INDEX_BEGIN = 1
    TH_TITLE_INDEX = 1
    TD_DATA_INDEX_BEGIN = 2
    TD_DATA_INDEX_END = 3

    def __init__(self):
        self._td_map = {}
        self._left_header_set = set()

    def parse(self, table: Selector):
        top_index_set = set()
        tr_list = table.css('tr')[self.TR_TITLE_INDEX_BEGIN:]

        for tr in tr_list:
            left_header = tr.css('th::text')[self.TH_TITLE_INDEX].get().strip()
            self._left_header_set.add(left_header)

            data_td_list = tr.css('td')[self.TD_DATA_INDEX_BEGIN:self.TD_DATA_INDEX_END]
            for top_index, td in enumerate(data_td_list):
                top_index_set.add(top_index)
                td_dict = self._td_map.setdefault(top_index, {})
                td_dict[left_header] = td

    def get_cell(self, top, left) -> Selector:
        try:
            return self._td_map[top][left]
        except KeyError as err:
            raise HeaderMismatchError(repr(err))

    def has_header(self, top=None, left=None) -> bool:
        return (top is None) and (left in self._left_header_set)


# ----------------------------------------------------------------------


class HistoryRoutingRule(BaseRoutingRule):
    name = 'HISTORY'

    @classmethod
    def build_routing_request(cls, mbl_no: str, container_no, view_state, jdt, cookies) -> RoutingRequest:
        form_data = {
            'cargoTrackListBean': 'cargoTrackListBean',
            'javax.faces.ViewState': view_state,
            jdt: jdt,
            'q_bl_no': mbl_no,
            'q_ctnr_no': container_no,
        }
        request = scrapy.FormRequest(
            url=f'{WHLC_BASE_URL}/cargoTrack/CargoTrackList.xhtml',
            method='POST',
            cookies=cookies,
            formdata=form_data,
            meta={
                'mbl_no': mbl_no,
                'container_key': container_no,
                'cookies': cookies,
            },
        )
        return RoutingRequest(request=request, rule_name=cls.name)

    def handle(self, response):
        container_key = response.meta['container_key']

        container_status_list = self._extract_container_status(response=response)
        for container_status in container_status_list:
            yield ContainerStatusItem(
                container_key=container_key,
                local_date_time=container_status['local_date_time'],
                description=container_status['description'],
                location=LocationItem(name=container_status['location_name']),
            )

    @staticmethod
    def _extract_container_status(response) -> List:
        container_key = response.meta['container_key']
        table_selector = response.css('table.tbl-list')

        if not table_selector:
            raise CarrierResponseFormatError(reason='container status table not found')

        table_locator = ContainerStatusTableLocator()
        table_locator.parse(table=table_selector)
        table = TableExtractor(table_locator=table_locator)

        return_list = []
        for left in table_locator.iter_left_headers():
            # text is too complicated to use re, maybe there's better solution
            description = table.extract_cell(top='Status Name', left=left).replace('\\n', '')
            description = ' '.join(description.split())
            local_date_time = table.extract_cell(top='Ctnr Date', left=left).replace('\\n', '')
            location_name = table.extract_cell(top='Ctnr Depot Name', left=left).replace('\\n', '')
            location_name = location_name.replace('\\t', '')

            return_list.append({
                'container_key': container_key,
                'local_date_time': local_date_time.strip(),
                'description': description.strip(),
                'location_name': location_name.strip(),
            })

        return return_list


class ContainerStatusTableLocator(BaseTableLocator):
    """
        +-----------------------------------+ <tbody>
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

    TR_TITLE_INDEX = 0
    TR_DATA_BEGIN_INDEX = 1

    def __init__(self):
        self._td_map = {}
        self._data_len = 0

    def parse(self, table: Selector):
        title_tr = table.css('tr')[self.TR_TITLE_INDEX]
        data_tr_list = table.css('tr')[self.TR_DATA_BEGIN_INDEX:]

        title_text_list = title_tr.css('th::text').getall()

        for title_index, title_text in enumerate(title_text_list):
            data_index = title_index

            title_text = title_text.strip()
            self._td_map[title_text] = []

            for data_tr in data_tr_list:
                data_td = data_tr.css('td')[data_index]

                self._td_map[title_text].append(data_td)

        self._data_len = len(data_tr_list)

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


class BaseMatchRule:

    @abc.abstractmethod
    def check(self, selector: scrapy.Selector) -> bool:
        pass


class NameOnTableMatchRule(BaseMatchRule):
    TABLE_NAME_QUERY = 'tr td a::text'

    def __init__(self, name: str):
        self.name = name

    def check(self, selector: scrapy.Selector) -> bool:
        table_name = selector.css(self.TABLE_NAME_QUERY).get()

        if not isinstance(table_name, str):
            return False

        return table_name.strip() == self.name


def find_selector_from(selectors: List[scrapy.Selector], rule: BaseMatchRule):
    for selector in selectors:
        if rule.check(selector=selector):
            return selector
    return None
