import re
from typing import Dict

import scrapy
from scrapy import Selector

from crawler.core_carrier.base_spiders import BaseCarrierSpider
from crawler.core_carrier.rules import RuleManager, RoutingRequest, BaseRoutingRule
from crawler.core_carrier.items import (
    BaseCarrierItem, MblItem, LocationItem, ContainerItem, ContainerStatusItem, DebugItem)
from crawler.core_carrier.exceptions import CarrierResponseFormatError, CarrierInvalidMblNoError
from crawler.extractors.table_extractors import BaseTableLocator, HeaderMismatchError, TableExtractor

RCL_BASE_URL = 'https://www.rclgroup.com'


class CarrierRclSpider(BaseCarrierSpider):
    name = 'carrier_rcl'

    def __init__(self, *args, **kwargs):
        super(CarrierRclSpider, self).__init__(*args, **kwargs)

        rules = [
            BasicRoutingRule(),
            MainInfoRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)

    def start(self):
        routing_request = BasicRoutingRule.build_routing_request(mbl_no=self.mbl_no)
        yield self._rule_manager.build_request_by(routing_request=routing_request)

    def parse(self, response):
        yield DebugItem(info={'meta': dict(response.meta)})

        routing_rule = self._rule_manager.get_rule_by_response(response=response)

        save_name = routing_rule.get_save_name(response=response)
        self._saver.save(to=save_name, text=response.text)

        for result in routing_rule.handle(response=response):
            if isinstance(result, BaseCarrierItem):
                yield result
            elif isinstance(result, RoutingRequest):
                yield self._rule_manager.build_request_by(routing_request=result)
            else:
                raise RuntimeError()


# -------------------------------------------------------------------------------

class BasicRoutingRule(BaseRoutingRule):
    name = 'BASIC'

    @classmethod
    def build_routing_request(cls, mbl_no: str) -> RoutingRequest:
        request = scrapy.Request(
            url=f'{RCL_BASE_URL}/Home',
            meta={'mbl_no': mbl_no},
        )
        return RoutingRequest(request=request, rule_name=cls.name)

    def get_save_name(self, response) -> str:
        return f'{self.name}.html'

    def handle(self, response):
        mbl_no = response.meta['mbl_no']

        main_info_endpoint = self._extract_main_info_endpoint(response=response)
        form_data = self._extract_form_data(response=response, mbl_no=mbl_no)

        yield MainInfoRoutingRule.build_routing_request(form_data=form_data, endpoint=main_info_endpoint)

    @staticmethod
    def _extract_main_info_endpoint(response: scrapy.Selector) -> str:
        pattern = re.compile(r'"(?P<endpoint>[^"]*Cargo_Tracking[^"]*)"')

        onclick_text = response.css('input[name="ctl00$ContentPlaceHolder1$ctrackbtn"]::attr(onclick)').get()

        if not onclick_text:
            raise CarrierResponseFormatError(reason='no onclick text')

        m = pattern.search(onclick_text)

        if not m:
            raise CarrierResponseFormatError(reason='pattern not search')

        endpoint = m.group('endpoint')
        return endpoint

    @staticmethod
    def _extract_form_data(response: scrapy.Selector, mbl_no: str) -> Dict:
        hidden_div_list = response.css('div[class=aspNetHidden]')
        captcha_value = response.css('input[name="ctl00$ContentPlaceHolder1$captchavalue"]::attr(value)').get()

        form_data = {}

        for div in hidden_div_list:
            for css_input in div.css('input'):
                name = css_input.css('::attr(name)').get()
                value = css_input.css('::attr(value)').get()
                form_data[name] = value

        form_data.update({
            'ctl00$ContentPlaceHolder1$cCaptcha': captcha_value,
            'ctl00$ContentPlaceHolder1$captchavalue': captcha_value,
            'ctl00$ContentPlaceHolder1$ctracking': mbl_no,
        })
        return form_data


# -------------------------------------------------------------------------------


class MainInfoRoutingRule(BaseRoutingRule):
    name = 'MAIN_INFO'

    @classmethod
    def build_routing_request(cls, form_data, endpoint) -> RoutingRequest:
        request = scrapy.FormRequest(
            url=f'{RCL_BASE_URL}/{endpoint}',
            formdata=form_data,
        )
        return RoutingRequest(request=request, rule_name=cls.name)

    def get_save_name(self, response) -> str:
        return f'{self.name}.html'

    def handle(self, response):
        self._check_mbl_no(response=response)

        main_info = self._extract_main_info(response=response)
        yield MblItem(
            mbl_no=main_info['mbl_no'],
            pol=LocationItem(name=main_info['pol_name']),
            pod=LocationItem(name=main_info['pod_name']),
            etd=main_info['etd'],
            eta=main_info['eta'],
        )

        container_info_dict = self._extract_container_info_dict(response=response)
        for container_no, container_status_list in container_info_dict.items():
            yield ContainerItem(
                container_key=container_no,
                container_no=container_no,
            )

            for container_status in container_status_list:
                yield ContainerStatusItem(
                    container_key=container_no,
                    local_date_time=container_status['local_date_time'],
                    description=container_status['description'],
                    location=LocationItem(name=container_status['location_name']),
                )

    @staticmethod
    def _check_mbl_no(response: scrapy.Selector):
        no_result_div = response.css('div#ContentPlaceHolder1_noresults')

        if no_result_div:
            raise CarrierInvalidMblNoError()

    @staticmethod
    def _extract_main_info(response: scrapy.Selector) -> Dict:
        table = response.css('table.bltable')[0]

        table_locator = MainInfoTableLocator()
        table_locator.parse(table=table)
        table_extractor = TableExtractor(table_locator=table_locator)

        # mbl_no
        mbl_no_pattern = re.compile(r'^Bill of Lading No[.] : (?P<mbl_no>\w+)')

        table_name = table_locator.get_table_name()

        m = mbl_no_pattern.match(table_name)
        if not m:
            raise CarrierResponseFormatError(reason=f'mbl_no not found : `{table_name}`')

        mbl_no = m.group('mbl_no')

        # other info
        location_index = 0
        date_index = 4

        return {
            'mbl_no': mbl_no,
            'pol_name': table_extractor.extract_cell(top=location_index, left='POL'),
            'pod_name': table_extractor.extract_cell(top=location_index, left='POD'),
            'etd': table_extractor.extract_cell(top=date_index, left='POL'),
            'eta': table_extractor.extract_cell(top=date_index, left='POD'),
        }

    @staticmethod
    def _extract_container_info_dict(response: scrapy.Selector) -> Dict:
        tables = response.css('table.regtable')

        container_pattern = re.compile(r'^Container No[.] : (?P<container_no>\w+)')

        return_dict = {}
        for table in tables:
            table_locator = ContainerStatusTableLocator()
            table_locator.parse(table=table)
            table_extractor = TableExtractor(table_locator=table_locator)

            # container_no
            table_name = table_locator.get_table_name()

            m = container_pattern.match(table_name)
            if not m:
                raise CarrierResponseFormatError(reason=f'container_no not found : `{table_name}`')

            container_no = m.group('container_no')

            return_dict.setdefault(container_no, [])

            # container status
            for left in table_locator.iter_left_headers():
                return_dict[container_no].append({
                    'local_date_time': table_extractor.extract_cell(top='Movement Date', left=left),
                    'description': table_extractor.extract_cell(top='Movement Detail', left=left),
                    'location_name': table_extractor.extract_cell(top='Movement Place', left=left),
                })

        return return_dict


class MainInfoTableLocator(BaseTableLocator):
    """
        +-------------------------------------+
        | Name                                | <tr>
        +-------+-------+-----+-----+----+----+
        | Title | Data  | ... |     |    |    | <tr>
        +-------+-------+-----+-----+----+----+
        | Title | Data  | ... |     |    |    | <tr>
        +-------+-------+-----+-----+----+----+
    """
    TR_DATA_INDEX_BEGIN = 1
    TR_DATA_INDEX_END = 3
    TD_INDEX_BEGIN = 1

    def __init__(self):
        self._td_map = {}   # top_index: {left_header: td, ...}
        self._left_header_set = set()
        self._table_name = ''

    def parse(self, table: Selector):
        self._table_name = table.css('tr th::text').get() or ''

        top_index_set = set()
        data_tr = table.css('tr')[self.TR_DATA_INDEX_BEGIN:self.TR_DATA_INDEX_END]
        for tr in data_tr:
            left_header = tr.css('td.bltablehead::text').get().strip()
            self._left_header_set.add(left_header)

            for top_index, td in enumerate(tr.css('td')[self.TD_INDEX_BEGIN:]):
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

    def get_table_name(self) -> str:
        return self._table_name


class ContainerStatusTableLocator(BaseTableLocator):
    """
        +-----------------------+
        | Name                  |
        +-------+-------+-------+
        | Title | Title | Title |
        +-------+-------+-------+
        | Data  |       |       |
        +-------+-------+-------+
        | ...   |       |       |
        +-------+-------+-------+
        | Data  |       |       |
        +-------+-------+-------+
    """
    TR_TITLE_INDEX = 1
    TR_DATA_BEGIN_INDEX = 2

    def __init__(self):
        self._td_map = {}   # title: data
        self._data_len = 0
        self._table_name = ''

    def parse(self, table: Selector):
        self._table_name = table.css('tr th::text').get() or ''

        title_td_list = table.css('tr')[self.TR_TITLE_INDEX].css('td.bltablehead')
        data_tr_list = table.css('tr')[self.TR_DATA_BEGIN_INDEX:]

        for title_index, title_td in enumerate(title_td_list):
            data_index = title_index

            title = title_td.css('::text').get()
            self._td_map[title] = []

            for data_tr in data_tr_list:
                data_td = data_tr.css('td')[data_index]

                self._td_map[title].append(data_td)

        self._data_len = len(data_tr_list)

    def get_cell(self, top, left) -> Selector:
        try:
            return self._td_map[top][left]
        except KeyError as err:
            raise HeaderMismatchError(repr(err))

    def has_header(self, top=None, left=None) -> bool:
        if top not in self._td_map:
            raise HeaderMismatchError(repr(KeyError))

        return left is None

    def iter_left_headers(self):
        for index in range(self._data_len):
            yield index

    def get_table_name(self) -> str:
        return self._table_name
