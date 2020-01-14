import re
from typing import Dict, List

import scrapy

from crawler.core_carrier.base_spiders import BaseCarrierSpider
from crawler.core_carrier.exceptions import CarrierInvalidMblNoError, CarrierResponseFormatError
from crawler.core_carrier.items import BaseCarrierItem, MblItem, ContainerItem, ContainerStatusItem, LocationItem, \
    VesselItem
from crawler.core_carrier.rules import RuleManager, RoutingRequest, BaseRoutingRule
from crawler.extractors.selector_finder import BaseMatchRule, find_selector_from, CssQueryTextStartswithMatchRule
from crawler.extractors.table_cell_extractors import FirstTextTdExtractor
from crawler.extractors.table_extractors import BaseTableLocator, HeaderMismatchError, TableExtractor

URL = 'https://www.shipcont.com/CCM.aspx'


class SharedSpider(BaseCarrierSpider):
    name = None

    def __init__(self, *args, **kwargs):
        super(SharedSpider, self).__init__(*args, **kwargs)

        rules = [
            MainInfoRoutingRule(),
            ContainerStatusRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)

    def start_requests(self):
        routing_request = MainInfoRoutingRule.build_routing_request(mbl_no=self.mbl_no)
        request = self._rule_manager.build_request_by(routing_request=routing_request)
        yield request

    def parse(self, response):
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


class CarrierSsphSpider(SharedSpider):
    name = 'carrier_ssph'


class CarrierGosuSpider(SharedSpider):
    name = 'carrier_gosu'


class MainInfoRoutingRule(BaseRoutingRule):
    name = 'MAIN_INFO'

    @classmethod
    def build_routing_request(cls, mbl_no) -> RoutingRequest:
        url = f'{URL}?hidSearch=true&hidFromHomePage=false&hidSearchType=1&id=166&l=4&textContainerNumber={mbl_no}'
        request = scrapy.Request(url=url)
        return RoutingRequest(request=request, rule_name=cls.name)

    def get_save_name(self, response) -> str:
        return f'{self.name}.html'

    def handle(self, response):
        self._check_main_info(response=response)

        mbl_no = self._extract_mbl_no(response=response)
        main_info = self._extract_main_info(response=response)

        yield MblItem(
            mbl_no=mbl_no or None,
            por=LocationItem(name=main_info['por_name']),
            pol=LocationItem(name=main_info['pol_name']),
            pod=LocationItem(name=main_info['pod_name']),
            final_dest=LocationItem(name=main_info['final_dest_name']),
        )

        vessel_info_list = self._extract_vessel_info_list(response=response)

        for vessel_info in vessel_info_list:
            yield VesselItem(
                vessel_key=vessel_info['vessel'],
                vessel=vessel_info['vessel'],
                voyage=vessel_info['voyage'],
                eta=vessel_info['eta'],
                etd=vessel_info['etd'],
                pol=LocationItem(name=vessel_info['pol_name']),
                pod=LocationItem(name=vessel_info['pod_name']),
            )

        container_info_list = self._extract_container_info(response=response)

        for container_info in container_info_list:
            container_no = container_info['container_no']
            yield ContainerItem(
                container_key=container_no,
                container_no=container_no,
            )

            eta = container_info['eta']
            yield ContainerStatusRoutingRule.build_routing_request(mbl_no=mbl_no, eta=eta, container_no=container_no)

    @staticmethod
    def _check_main_info(response):
        data_found_selector = response.css('table#tbPrint')
        if not data_found_selector:
            raise CarrierInvalidMblNoError()

    @staticmethod
    def _extract_mbl_no(response):
        pattern = re.compile(r'^B/L Number (?P<mbl_no>\w+)$')

        rule = CssQueryTextStartswithMatchRule(css_query='strong::text', startswith='B/L Number')
        selector = find_selector_from(selectors=response.css('td.BlackText'), rule=rule)

        if not selector:
            return ''

        mbl_no_text = selector.css('strong::text').get()
        m = pattern.match(mbl_no_text)
        if not m:
            raise CarrierResponseFormatError('mbl_no not match')

        mbl_no = m.group('mbl_no')
        return mbl_no

    @staticmethod
    def _extract_main_info(response) -> Dict:
        rule = FirstTitleMatchRule(first_title='Place of Receipt')
        table = find_selector_from(selectors=response.css('td #tbPrint'), rule=rule)

        table_locator = TrDataTableLocator()
        table_locator.parse(table=table)
        table_extractor = TableExtractor(table_locator=table_locator)

        return {
            'por_name': table_extractor.extract_cell(top='Place of Receipt', left=0) or None,
            'pol_name': table_extractor.extract_cell(top='Port of Loading', left=0) or None,
            'pod_name': table_extractor.extract_cell(top='Port of Destination', left=0) or None,
            'final_dest_name': table_extractor.extract_cell(top='Final Destination', left=0) or None,
        }

    def _extract_vessel_info_list(self, response) -> List:
        match_rule = FirstTitleMatchRule(first_title='Local Departure')
        table = find_selector_from(selectors=response.css('td #tbPrint'), rule=match_rule)

        table_locator = TrDataTableLocator()
        table_locator.parse(table=table)
        table_extractor = TableExtractor(table_locator=table_locator)

        return_list = []
        for left in table_locator.iter_left_headers():

            vessel_voyage = table_extractor.extract_cell(top='Vessel & Voyage', left=left)

            vessel_voyage_pattern = re.compile(r'^(?P<vessel>.+)/(?P<voyage>.+)$')
            vessel_voyage_match = vessel_voyage_pattern.match(vessel_voyage)

            if vessel_voyage_match:
                vessel = vessel_voyage_match.group('vessel')
                voyage = vessel_voyage_match.group('voyage')

                etd_text = table_extractor.extract_cell(top='Local Departure', left=left)
                eta_text = table_extractor.extract_cell(top='Local Arrival', left=left)

                etd, pol = self._get_local_date_time_and_location(local_date_time_text=etd_text)
                eta, pod = self._get_local_date_time_and_location(local_date_time_text=eta_text)

                return_list.append({
                    'etd': etd,
                    'eta': eta,
                    'vessel': vessel,
                    'voyage': voyage,
                    'pol_name': pol,
                    'pod_name': pod,
                })

        return return_list

    @staticmethod
    def _extract_container_info(response) -> List:
        match_rule = FirstTitleMatchRule(first_title='Container No.')
        table = find_selector_from(selectors=response.css('td #tbPrint'), rule=match_rule)

        table_locator = TrDataTableLocator()
        table_locator.parse(table=table)
        table_extractor = TableExtractor(table_locator=table_locator)

        first_text_td_extractor = FirstTextTdExtractor()
        a_text_td_extractor = FirstTextTdExtractor(css_query='a::text')

        return_list = []
        for left in table_locator.iter_left_headers():
            return_list.append({
                'container_no': table_extractor.extract_cell(
                    top='Container No.', left=left, extractor=a_text_td_extractor),
                'eta': table_extractor.extract_cell(
                    top='Estimated Arrival Date', left=left, extractor=first_text_td_extractor),
            })

        return return_list

    @staticmethod
    def _get_local_date_time_and_location(local_date_time_text: str):
        pattern = re.compile(r'^(?P<local_date_time>\d{2}-\w{3}-\d{4}), (?P<location>.+)$')

        m = pattern.match(local_date_time_text)
        if m:
            local_date_time = m.group('local_date_time')
            location = m.group('location')
        else:
            local_date_time = None
            location = local_date_time_text

        return local_date_time, location


class ContainerStatusRoutingRule(BaseRoutingRule):
    name = 'CONTAINER_STATUS'

    @classmethod
    def build_routing_request(cls, mbl_no, eta, container_no) -> RoutingRequest:
        url = f'{URL}?&id=166&l=4&conNum={container_no}&blNum={mbl_no}&eta={eta}&inbId=&searchType=3'
        request = scrapy.Request(url=url, meta={'container_key': container_no})
        return RoutingRequest(request=request, rule_name=cls.name)

    def get_save_name(self, response) -> str:
        container_no = response.meta['container_key']
        return f'{self.name}_{container_no}.html'

    def handle(self, response):
        container_key = response.meta['container_key']
        container_status_list = self._extract_container_status(response=response)

        for status in container_status_list:
            yield ContainerStatusItem(
                container_key=container_key,
                description=status['description'],
                location=LocationItem(name=status['location_name']),
                local_date_time=status['local_date_time'],
            )

    @staticmethod
    def _extract_container_status(response) -> List:
        match_rule = FirstTitleMatchRule(first_title='Activity')
        table = find_selector_from(selectors=response.css('td #tbPrint'), rule=match_rule)

        table_locator = TrDataTableLocator()
        table_locator.parse(table=table)
        table_extractor = TableExtractor(table_locator=table_locator)
        td_extractor = FirstTextTdExtractor()

        return_list = []
        for left in table_locator.iter_left_headers():
            return_list.append({
                'description': table_extractor.extract_cell(top='Activity', left=left, extractor=td_extractor),
                'location_name': table_extractor.extract_cell(top='Location', left=left, extractor=td_extractor),
                'local_date_time': table_extractor.extract_cell(top='Date', left=left, extractor=td_extractor),
            })

        return return_list


class TrDataTableLocator(BaseTableLocator):
    """
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
       +---------+---------+-----+---------+
    """

    TR_DATA_BEGIN = 1

    def __init__(self):
        self._td_map = {}
        self._data_len = 0

    def parse(self, table: scrapy.Selector):
        title_td_list = table.css('tr')[0].css('td strong')
        data_tr_list = table.css('tr')[self.TR_DATA_BEGIN:].css('[bgcolor]')

        for title_index, title_td in enumerate(title_td_list):
            data_index = title_index

            title = title_td.css('::text').get().strip()
            self._td_map[title] = []

            for data_tr in data_tr_list:
                data_td = data_tr.css('td')[data_index]

                self._td_map[title].append(data_td)

        self._data_len = len(data_tr_list)

    def get_cell(self, top, left) -> scrapy.Selector:
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


class FirstTitleMatchRule(BaseMatchRule):
    FIRST_TITLE_TEXT_QUERY = 'tr td strong::text'

    def __init__(self, first_title: str):
        self.first_title = first_title

    def check(self, selector: scrapy.Selector) -> bool:
        first_title = selector.css(self.FIRST_TITLE_TEXT_QUERY)[0].get()

        if not isinstance(first_title, str):
            return False

        return first_title.strip() == self.first_title
