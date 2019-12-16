import json
from typing import Dict

import scrapy
from scrapy import Selector

from crawler.core_carrier.base_spiders import BaseCarrierSpider
from crawler.core_carrier.rules import RuleManager, RoutingRequest, BaseRoutingRule
from crawler.core_carrier.items import (
    BaseCarrierItem, MblItem, LocationItem, VesselItem, ContainerItem, ContainerStatusItem)
from crawler.core_carrier.exceptions import CarrierResponseFormatError, CarrierInvalidMblNoError

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from crawler.core_carrier.exceptions import LoadWebsiteTimeOutError
from crawler.extractors.table_cell_extractors import BaseTableCellExtractor
from crawler.extractors.table_extractors import BaseTableLocator, HeaderMismatchError, TableExtractor
from crawler.utils.decorators import merge_yields

PABV_BASE_URL = 'https://www.pilship.com'


class CarrierPabvSpider(BaseCarrierSpider):
    name = 'carrier_pabv'

    def __init__(self, *args, **kwargs):
        super(CarrierPabvSpider, self).__init__(*args, **kwargs)

        rules = [
            TrackRoutingRule(),
            ContainerRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)

    def start_requests(self):
        cookies_getter = CookiesGetter()
        cookies = cookies_getter.get_cookies()

        routing_request = TrackRoutingRule.build_routing_request(mbl_no=self.mbl_no, cookies=cookies)
        yield self._rule_manager.build_request_by(routing_request=routing_request)

    @merge_yields
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


# -------------------------------------------------------------------------------


class TrackRoutingRule(BaseRoutingRule):
    name = 'TRACK'

    @classmethod
    def build_routing_request(cls, mbl_no: str, cookies: dict) -> RoutingRequest:
        request = scrapy.Request(
            url=f'{PABV_BASE_URL}/shared/ajax/?fn=get_tracktrace_bl&ref_num={mbl_no}',
            cookies=cookies,
            meta={'cookies': cookies},
        )
        return RoutingRequest(request=request, rule_name=cls.name)

    def get_save_name(self, response) -> str:
        return f'{self.name}.html'

    def handle(self, response):
        cookies = response.meta['cookies']

        try:
            response_dict = json.loads(response.text)
        except json.JSONDecodeError:
            raise CarrierResponseFormatError('cookies are expired')

        content = response_dict['data']
        if content['err'] != 0:
            raise CarrierInvalidMblNoError()

        mbl_no = content['refnum']['0']
        schedule_info = self._extract_schedule_info(content=content)
        por = schedule_info['Place of Receipt']
        place_of_deliv = schedule_info['Place of Delivery']

        yield MblItem(
            mbl_no=mbl_no,
            por=LocationItem(name=por['name'], un_lo_code=por['un_lo_code']),
            place_of_deliv=LocationItem(name=place_of_deliv['name'], un_lo_code=place_of_deliv['un_lo_code']),
        )

        for schedule_table in self._extract_schedule_table(content=content):
            vessel = schedule_table['vessel']
            pol = schedule_table['pol']
            pod = schedule_table['pod']

            yield VesselItem(
                vessel_key=vessel,
                vessel=vessel,
                voyage=schedule_table['voyage'],
                pol=LocationItem(name=pol['name'], un_lo_code=pol['un_lo_code']),
                pod=LocationItem(un_lo_code=pod['un_lo_code']),
                etd=schedule_table['etd'],
                eta=schedule_table['eta'],
            )

        container_ids = self._extract_containers(content=content)
        for container_id in container_ids:
            yield ContainerItem(container_key=container_id, container_no=container_id)
            yield ContainerRoutingRule.build_routing_request(mbl_no=mbl_no, cookies=cookies, container_id=container_id)

    @staticmethod
    def _extract_schedule_info(content):
        data = content['scheduleinfo']

        lines = data.split('<br />')

        schedule_info = {}
        for line in lines:
            if not line:
                continue

            values = line.strip().split('<b>')

            key = values[0].strip()
            name = values[1].split('[')[0].strip()
            un_lo_code = values[1].split(']')[0].split('[')[-1]

            schedule_info[key] = {'name': name, 'un_lo_code': un_lo_code}

        return schedule_info

    @staticmethod
    def _extract_schedule_table(content) -> Dict:
        selector = Selector(text=content['scheduletable'])

        schedule_table_locator = TopHeaderStyleTableLocator(header_style_map={
            'Arrival/Delivery': 'arrival-delivery',
            'Location': 'location',
            'Vessel/Voyage': 'vessel-voyage',
            'Next Location': 'next-location',
        })
        schedule_table_locator.parse(table=selector)
        schedule_table_extractor = TableExtractor(table_locator=schedule_table_locator)

        cell_extractor = ScheduleTableCellExtractor()

        for left in schedule_table_locator.iter_left_headers():
            pol = {
                'name': schedule_table_extractor.extract_cell('Location', left, extractor=cell_extractor)[1],
                'un_lo_code': schedule_table_extractor.extract_cell('Location', left, extractor=cell_extractor)[2],
            }
            pod = {
                'un_lo_code': schedule_table_extractor.extract_cell('Next Location', left, extractor=cell_extractor)[0],
            }
            yield {
                'etd': schedule_table_extractor.extract_cell('Arrival/Delivery', left, extractor=cell_extractor)[1],
                'pol': pol,
                'vessel': schedule_table_extractor.extract_cell('Vessel/Voyage', left, extractor=cell_extractor)[0],
                'voyage': schedule_table_extractor.extract_cell('Vessel/Voyage', left, extractor=cell_extractor)[1],
                'pod': pod,
                'eta': schedule_table_extractor.extract_cell('Next Location', left, extractor=cell_extractor)[1],
            }

    @staticmethod
    def _extract_containers(content):
        selector = Selector(text=content['containers'])

        container_ids = []
        for result_row in selector.xpath('//tr[@class="resultrow"]'):
            container_id = result_row.xpath('./td/table/tr/td/b/text()').get()
            container_ids.append(container_id)

        return container_ids


# -------------------------------------------------------------------------------


class ContainerRoutingRule(BaseRoutingRule):
    name = 'CONTAINER'

    @classmethod
    def build_routing_request(cls, mbl_no: str, cookies: dict, container_id: str) -> RoutingRequest:
        request = scrapy.Request(
            url=(
                f'{PABV_BASE_URL}/shared/ajax/?fn=get_track_container_status&search_type=bl'
                f'&search_type_no={mbl_no}&ref_num={container_id}'
            ),
            cookies=cookies,
            meta={'container_id': container_id},
        )
        return RoutingRequest(request=request, rule_name=cls.name)

    def get_save_name(self, response) -> str:
        container_id = response.meta['container_id']
        return f'{self.name}_{container_id}.html'

    def handle(self, response):
        container_id = response.meta['container_id']

        try:
            content = json.loads(response.text)
        except json.JSONDecodeError:
            raise CarrierResponseFormatError("cookies are expired")

        for container_item in self._extract_container_table(content):
            yield ContainerStatusItem(
                container_key=container_id,
                description=container_item['description'],
                local_date_time=container_item['local_date_time'],
                location=LocationItem(name=container_item['location']),
                transport=container_item['transport'],
                est_or_actual=container_item['est_or_actual'],
            )

    @staticmethod
    def _extract_container_table(content) -> Dict:
        selector = Selector(text=content['data']['events_table'])

        schedule_table_locator = TopHeaderStyleTableLocator(header_style_map={
            'Container #': 'container-num',
            'Date': 'date',
            'Latest Event': 'latest-event',
            'Place': 'place',
        })
        schedule_table_locator.parse(table=selector)
        schedule_table_extractor = TableExtractor(table_locator=schedule_table_locator)

        for left in schedule_table_locator.iter_left_headers():
            date_str = schedule_table_extractor.extract_cell('Date', left)

            if date_str == 'Pending':
                continue
            elif '*' in date_str:
                date_str = date_str.strip('* ')
                est_or_actual = 'E'
            else:
                est_or_actual = 'A'

            yield {
                'transport': schedule_table_extractor.extract_cell('Container #', left),
                'description': schedule_table_extractor.extract_cell('Latest Event', left),
                'local_date_time': date_str,
                'location': schedule_table_extractor.extract_cell('Place', left),
                'est_or_actual': est_or_actual,
            }


# -------------------------------------------------------------------------------

class CookiesGetter:

    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--disable-extensions')
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')

        self._browser = webdriver.Chrome(chrome_options=options)

    def get_cookies(self):

        self._browser.get(f'{PABV_BASE_URL}/en-our-track-and-trace-pil-pacific-international-lines/120.html')
        try:
            WebDriverWait(self._browser, 10).until(self._is_cookies_ready)
        except TimeoutException:
            raise LoadWebsiteTimeOutError()

        cookies = {}
        for cookie_object in self._browser.get_cookies():
            cookies[cookie_object['name']] = cookie_object['value']

        self._browser.close()
        return cookies

    def _is_cookies_ready(self, *_):
        cookies_str = str(self._browser.get_cookies())
        return ('front_www_pilship_com' in cookies_str) and ('TS01a292b3' in cookies_str)


# -------------------------------------------------------------------------------


class TopHeaderStyleTableLocator(BaseTableLocator):
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

    def __init__(self, header_style_map: Dict[str, str]):
        self._header_style_map = header_style_map

        self._td_map = {
            top_header: [] for top_header in self._header_style_map
        }
        self._data_len = 0

    def parse(self, table: scrapy.Selector):
        tr_list = table.css('tr')

        self._data_len = len(tr_list)

        for tr in tr_list:
            for top_header, style in self._header_style_map.items():
                td = tr.css(f'td.{style}')
                self._td_map[top_header].append(td)

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


class ScheduleTableCellExtractor(BaseTableCellExtractor):
    def extract(self, cell: Selector):
        return cell.css('::text').getall()
