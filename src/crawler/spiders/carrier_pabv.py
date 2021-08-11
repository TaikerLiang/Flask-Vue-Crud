import json
from typing import Dict

import scrapy
from scrapy import Selector
from urllib3.exceptions import ReadTimeoutError

from crawler.core_carrier.base_spiders import BaseCarrierSpider
from crawler.core_carrier.request_helpers import ProxyManager, RequestOption
from crawler.core_carrier.rules import RuleManager, BaseRoutingRule
from crawler.core_carrier.items import (
    BaseCarrierItem,
    MblItem,
    LocationItem,
    VesselItem,
    ContainerItem,
    ContainerStatusItem,
    DebugItem,
)
from crawler.core_carrier.exceptions import (
    CarrierResponseFormatError,
    CarrierInvalidMblNoError,
    SuspiciousOperationError,
    LoadWebsiteTimeOutError,
)

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from crawler.extractors.table_cell_extractors import BaseTableCellExtractor, FirstTextTdExtractor
from crawler.extractors.table_extractors import BaseTableLocator, HeaderMismatchError, TableExtractor


PABV_BASE_URL = 'https://www.pilship.com'


class CarrierPabvSpider(BaseCarrierSpider):
    name = 'carrier_pabv'

    def __init__(self, *args, **kwargs):
        super(CarrierPabvSpider, self).__init__(*args, **kwargs)

        self._proxy_manager = ProxyManager(session='pabv', logger=self.logger)

        rules = [
            TrackRoutingRule(),
            ContainerRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)

    def start(self):
        while True:
            self._proxy_manager.renew_proxy()

            # cookies_getter = CookiesGetter(phantom_js_service_args=self._proxy_manager.get_phantom_js_service_args())
            cookies_getter = CookiesGetter()

            try:
                cookies = cookies_getter.get_cookies()
            except (LoadWebsiteTimeOutError, ReadTimeoutError):
                continue

            option = TrackRoutingRule.build_request_option(mbl_no=self.mbl_no, cookies=cookies)
            proxy_option = self._proxy_manager.apply_proxy_to_request_option(option=option)
            yield self._build_request_by(option=proxy_option)

            break

    def parse(self, response):
        yield DebugItem(info={'meta': dict(response.meta)})

        routing_rule = self._rule_manager.get_rule_by_response(response=response)

        save_name = routing_rule.get_save_name(response=response)
        self._saver.save(to=save_name, text=response.text)

        for result in routing_rule.handle(response=response):
            if isinstance(result, BaseCarrierItem):
                yield result
            elif isinstance(result, RequestOption):
                proxy_option = self._proxy_manager.apply_proxy_to_request_option(option=result)
                yield self._build_request_by(option=proxy_option)
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
                headers=option.headers,
                cookies=option.cookies,
                meta=meta,
                callback=self.parse,
            )
        else:
            raise SuspiciousOperationError(msg=f'Unexpected request method: `{option.method}`')


# -------------------------------------------------------------------------------


class TrackRoutingRule(BaseRoutingRule):
    name = 'TRACK'

    @classmethod
    def build_request_option(cls, mbl_no, cookies: dict) -> RequestOption:
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=f'{PABV_BASE_URL}/shared/ajax/?fn=get_tracktrace_bl&ref_num={mbl_no}',
            cookies=cookies,
            meta={
                'cookies': cookies,
            },
        )

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
            yield ContainerRoutingRule.build_request_option(mbl_no=mbl_no, cookies=cookies, container_id=container_id)

    @staticmethod
    def _extract_schedule_info(content):
        data = content['scheduleinfo']

        schedule_info_selector = scrapy.Selector(text=data)

        schedule_info = {}
        por_value = schedule_info_selector.css('td::text')[0].get()
        por_name = por_value.split('[')[0].strip()
        por_un_lo_code = por_value.split(']')[0].split('[')[-1]
        schedule_info['Place of Receipt'] = {'name': por_name, 'un_lo_code': por_un_lo_code}

        del_value = schedule_info_selector.css('td::text')[1].get()
        del_name = del_value.split('[')[0].strip()
        del_un_lo_code = del_value.split(']')[0].split('[')[-1]
        schedule_info['Place of Delivery'] = {'name': del_name, 'un_lo_code': del_un_lo_code}

        return schedule_info

    @staticmethod
    def _extract_schedule_table(content) -> Dict:
        selector = Selector(text=content['scheduletable'])

        schedule_table_locator = TopHeaderStyleTableLocator(
            header_style_map={
                'Arrival/Delivery': 'arrival-delivery',
                'Location': 'location',
                'Vessel/Voyage': 'vessel-voyage',
                'Next Location': 'next-location',
            }
        )
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
        for container_id in selector.xpath('//tbody/tr/td/b/text()'):
            container_ids.append(container_id.get())

        return container_ids


# -------------------------------------------------------------------------------


class ContainerRoutingRule(BaseRoutingRule):
    name = 'CONTAINER'

    @classmethod
    def build_request_option(cls, mbl_no: str, cookies: dict, container_id: str) -> RequestOption:
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=(
                f'{PABV_BASE_URL}/shared/ajax/?fn=get_track_container_status&search_type=bl'
                f'&search_type_no={mbl_no}&ref_num={container_id}'
            ),
            cookies=cookies,
            meta={
                'container_id': container_id,
            },
        )

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
                est_or_actual=container_item['est_or_actual'],
            )

    @staticmethod
    def _extract_container_table(content) -> Dict:
        selector = Selector(text=content['data']['events_table'])

        schedule_table_locator = TopHeaderTableLocator()
        schedule_table_locator.parse(table=selector)
        schedule_table_extractor = TableExtractor(table_locator=schedule_table_locator)

        for left in schedule_table_locator.iter_left_headers():
            date_str = schedule_table_extractor.extract_cell('Event Date', left)

            if date_str == 'Pending':
                continue
            elif '*' in date_str:
                date_str = date_str.strip('* ')
                est_or_actual = 'E'
            else:
                est_or_actual = 'A'

            yield {
                'description': schedule_table_extractor.extract_cell('Event Name', left),
                'local_date_time': date_str,
                'location': schedule_table_extractor.extract_cell('Event Location', left),
                'est_or_actual': est_or_actual,
            }


# -------------------------------------------------------------------------------


class CookiesGetter:

    TIMEOUT = 40

    def __init__(self):
        # self._browser = webdriver.PhantomJS(service_args=phantom_js_service_args)
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
            WebDriverWait(self._browser, self.TIMEOUT).until(self._is_cookies_ready)
        except TimeoutException:
            raise LoadWebsiteTimeOutError(url=self._browser.current_url)

        cookies = {}
        for cookie_object in self._browser.get_cookies():
            cookies[cookie_object['name']] = cookie_object['value']

        self._browser.close()
        return cookies

    def _is_cookies_ready(self, *_):
        cookies_str = str(self._browser.get_cookies())
        return ('TS018fa092' in cookies_str) and ('front_www_pilship_com' in cookies_str)


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

        self._td_map = {top_header: [] for top_header in self._header_style_map}
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

class TopHeaderTableLocator(BaseTableLocator):
    def __init__(self):
        self._td_map = {}  # top_header: [td, ...]
        self._data_len = 0

    def parse(self, table: Selector):
        top_header_list = []

        head = table.css('tr.text-fw-bold')
        for th in head.css('td'):
            raw_top_header = th.css('::text').get()
            top_header = raw_top_header.strip() if isinstance(raw_top_header, str) else ''
            top_header_list.append(top_header)
            self._td_map[top_header] = []

        body = table.css('tr:not(.text-fw-bold)')
        for tr in body:
            for top_index, td in enumerate(tr.css('td')):
                top = top_header_list[top_index]
                self._td_map[top].append(td)

        self._data_len = len(body)

    def get_cell(self, top, left) -> Selector:
        try:
            if not self._td_map[top]:
                return scrapy.Selector(text='<td></td>')

            return self._td_map[top][left]
        except (KeyError, IndexError) as err:
            raise HeaderMismatchError(repr(err))

    def has_header(self, top=None, left=None) -> bool:
        return (top in self._td_map) and (left is None)

    def iter_left_headers(self):
        for i in range(self._data_len):
            yield i


class ScheduleTableCellExtractor(BaseTableCellExtractor):
    def extract(self, cell: Selector):
        return cell.css('::text').getall()
