import re
from typing import Dict

import scrapy
from scrapy import Selector

from crawler.core_carrier.base_spiders import BaseCarrierSpider
from crawler.core_carrier.rules import RuleManager, RoutingRequest, BaseRoutingRule
from crawler.core_carrier.items import (
    BaseCarrierItem, LocationItem, ContainerItem, ContainerStatusItem)
from crawler.core_carrier.exceptions import CarrierResponseFormatError, CarrierInvalidMblNoError
from crawler.core_carrier.exceptions import LoadWebsiteTimeOutError

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException

from crawler.extractors.table_cell_extractors import BaseTableCellExtractor, FirstTextTdExtractor
from crawler.extractors.table_extractors import BaseTableLocator, HeaderMismatchError, TableExtractor, \
    TopHeaderTableLocator


BASE_URL = 'https://www.hapag-lloyd.com/en/online-business'


class CarrierHlcuSpider(BaseCarrierSpider):
    name = 'carrier_hlcu'

    def __init__(self, *args, **kwargs):
        super(CarrierHlcuSpider, self).__init__(*args, **kwargs)

        rules = [
            TracingRoutingRule(),
            ContainerRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)

    def start_requests(self):
        cookies_getter = CookiesGetter()
        cookies = cookies_getter.get_cookies()

        routing_request = TracingRoutingRule.build_routing_request(mbl_no=self.mbl_no, cookies=cookies)
        yield self._rule_manager.build_request_by(routing_request=routing_request)

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


class TracingRoutingRule(BaseRoutingRule):
    name = 'TRACING'

    def __init__(self):
        self._cookies_pattern = re.compile(r'^(?P<key>[^=]+)=(?P<value>[^;]+);.+$')

    @classmethod
    def build_routing_request(cls, mbl_no: str, cookies: Dict) -> RoutingRequest:
        request = scrapy.Request(
            url=f'{BASE_URL}/tracing/tracing-by-booking.html?blno={mbl_no}',
            cookies=cookies,
            meta={'mbl_no': mbl_no, 'cookies': cookies},
        )
        return RoutingRequest(request=request, rule_name=cls.name)

    def get_save_name(self, response):
        return f'{self.name}.html'

    def handle(self, response):
        cookies = response.meta['cookies']
        mbl_no = response.meta['mbl_no']

        self._check_mbl_no(response)

        container_nos = self._extract_container_nos(response=response)
        for container_no in container_nos:
            yield ContainerItem(
                container_no=container_no,
                container_key=container_no,
            )

        new_cookies = self._handle_cookies(cookies=cookies, response=response)
        view_state = response.css(
            'form[id="tracing_by_booking_f"] input[name="javax.faces.ViewState"] ::attr(value)').get()

        for container_index, container_no in enumerate(container_nos):
            yield ContainerRoutingRule.build_routing_request(
                mbl_no=mbl_no,
                container_key=container_no,
                cookies=new_cookies,
                container_index=container_index,
                view_state=view_state,
            )

    @staticmethod
    def _check_mbl_no(response):
        error_message = response.css('span[id="tracing_by_booking_f:hl15"]::text').get()
        if not error_message:
            return

        error_message.strip()
        if error_message.startwith('DOCUMENT does not exist.'):
            raise CarrierInvalidMblNoError()

    @staticmethod
    def _extract_container_nos(response):
        table_selector = response.css("table[id='tracing_by_booking_f:hl27']")
        if not table_selector:
            raise CarrierResponseFormatError(reason=f'Container list table not found !!!')

        table_locator = TopHeaderTableLocator()
        table_locator.parse(table=table_selector)
        table = TableExtractor(table_locator=table_locator)
        span_extractor = FirstTextTdExtractor('span::text')

        container_list = []
        for left in table_locator.iter_left_header():
            container_no_text = table.extract_cell(top='Container No.', left=left, extractor=span_extractor)
            company, no = container_no_text.split()
            container_list.append(company + no)

        return container_list

    def _handle_cookies(self, cookies, response):
        cookie_bytes = response.headers.getlist('Set-Cookie')

        for cookie_byte in cookie_bytes:
            cookie_text = cookie_byte.decode('utf-8')
            key, value = self._parse_cookie(cookie_text=cookie_text)
            cookies[key] = value

        return cookies

    def _parse_cookie(self, cookie_text):
        """
        Sample 1: `TS01a3c52a=01541c804a3dfa684516e96cae7a588b5eea6236b8843ebfc7882ca3e47063c4b3fddc7cc2e58145e71bee297`
                  `3391cc28597744f23343d7d2544d27a2ce90ca4b356ffb78f5; Path=/`
        Sample 2: `TSff5ac71e_27=081ecde62cab2000428f3620d78d07ee66ace44f9dc6c6feb6bc1bab646fbc7179082123944d1473084a`
                  `f55ddf1120009050da999bcc34164749e3339b930c12ec88cf3b1cfb6cd3b77b94f5d061834e;Path=/`
        """
        match = self._cookies_pattern.match(cookie_text)
        if not match:
            CarrierResponseFormatError(f'Unknown cookie format: `{cookie_text}`')

        return match.group('key'), match.group('value')


class ContainerNoTdExtractor(BaseTableCellExtractor):

    def extract(self, cell: Selector):
        raw_text = cell.css('::text').get()
        text_list = raw_text.split()
        text = ''.join(text_list)

        return text


# -------------------------------------------------------------------------------


class ContainerRoutingRule(BaseRoutingRule):
    name = 'CONTAINER'

    @classmethod
    def build_routing_request(
            cls, mbl_no: str, container_key, cookies: Dict, container_index, view_state) -> RoutingRequest:
        form_data = {
            'hl27': str(container_index),
            'javax.faces.ViewState': view_state,
            'tracing_by_booking_f:hl16': mbl_no,
            'tracing_by_booking_f:hl27:hl53': 'Details',
            'tracing_by_booking_f_SUBMIT': '1',
        }
        request = scrapy.FormRequest(
            url=f'{BASE_URL}/tracing/tracing-by-booking.html?_a=tracing_by_booking',
            formdata=form_data,
            cookies=cookies,
            meta={'container_key': container_key}
        )
        return RoutingRequest(request=request, rule_name=cls.name)

    def get_save_name(self, response):
        container_key = response.meta['container_key']
        return f'{self.name}_{container_key}.html'

    def handle(self, response):
        container_key = response.meta['container_key']

        container_statuses = self._extract_container_statuses(response=response)
        for container_status in container_statuses:
            yield ContainerStatusItem(
                container_key=container_key,
                description=container_status['description'],
                local_date_time=container_status['timestamp'],
                location=LocationItem(name=container_status['place']),
                transport=container_status['transport'],
                voyage=container_status['voyage'],
                est_or_actual=container_status['est_or_actual'],
            )

    def _extract_container_statuses(self, response):
        table_selector = response.css("table[id='tracing_by_booking_f:hl66']")
        if not table_selector:
            CarrierResponseFormatError(reason='Can not find container_status table !!!')

        table_locator = ContainerStatusTableLocator()
        table_locator.parse(table=table_selector)
        table = TableExtractor(table_locator=table_locator)
        span_extractor = FirstTextTdExtractor(css_query='span::text')

        container_statuses = []
        for left in table_locator.iter_left_header():
            date = table.extract_cell(top='Date', left=left, extractor=span_extractor)
            time = table.extract_cell(top='Time', left=left, extractor=span_extractor)
            class_name = table_locator.get_row_class(left=left)

            container_statuses.append({
                'description': table.extract_cell(top='Status', left=left, extractor=span_extractor),
                'place': table.extract_cell(top='Place of Activity', left=left, extractor=span_extractor),
                'timestamp': f'{date} {time}',
                'transport': table.extract_cell(top='Transport', left=left, extractor=span_extractor),
                'voyage': table.extract_cell(top='Voyage No.', left=left, extractor=span_extractor) or None,
                'est_or_actual': self._get_status_from(class_name),
            })

        return container_statuses

    @staticmethod
    def _get_status_from(class_name):
        if class_name == 'strong':
            return 'A'
        elif not class_name:
            return 'E'
        else:
            raise CarrierResponseFormatError(reason=f'Unknown status: `{class_name}`')


class ContainerStatusTableLocator(BaseTableLocator):

    def __init__(self):
        self._td_map = {}  # title: [td, ...]
        self._tr_classes = []
        self._data_len = 0

    def parse(self, table: Selector):
        title_list = []
        tr_classes = []

        th_list = table.css('thead th')
        for th in th_list:
            title = th.css('span::text').get().strip()
            title_list.append(title)
            self._td_map[title] = []

        data_tr_list = table.css('tbody tr')
        for data_tr in data_tr_list:

            tr_class_set = set()
            data_td_list = data_tr.css('td')
            for title_index, data_td in enumerate(data_td_list):
                data_td_class = data_td.css('td::attr(class)').get()
                tr_class_set.add(data_td_class)

                title = title_list[title_index]
                self._td_map[title].append(data_td)

            tr_classes.append(list(tr_class_set)[0])

        self._tr_classes = tr_classes
        self._data_len = len(data_tr_list)

    def get_cell(self, top, left) -> Selector:
        try:
            return self._td_map[top][left]
        except (KeyError, IndexError) as err:
            raise HeaderMismatchError(repr(err))

    def has_header(self, top=None, left=None) -> bool:
        return (top in self._td_map) and (left is None)

    def iter_left_header(self):
        for i in range(self._data_len):
            yield i

    def get_row_class(self, left):
        return self._tr_classes[left]


# -------------------------------------------------------------------------------

class CookiesGetter:

    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--disable-extensions')
        # options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')

        self._browser = webdriver.Chrome(chrome_options=options)

    def get_cookies(self):
        self._browser.get(f'{BASE_URL}/tracing/tracing-by-booking.html')

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
        return ('TS01a3c52a' in cookies_str) and ('TSa4b927ad_76' in cookies_str) and ('TSPD_101' in cookies_str) and (
                    'TSff5ac71e_27' in cookies_str)