import re
import time
from typing import List, Dict

import scrapy
from scrapy import Selector
from selenium import webdriver

from crawler.core_carrier.base import CARRIER_RESULT_STATUS_FATAL, SHIPMENT_TYPE_MBL, SHIPMENT_TYPE_BOOKING
from crawler.core_carrier.base_spiders import (
    BaseCarrierSpider, CARRIER_DEFAULT_SETTINGS, DISABLE_DUPLICATE_REQUEST_FILTER)
from crawler.core_carrier.request_helpers import RequestOption
from crawler.core_carrier.rules import RuleManager, BaseRoutingRule, RequestOptionQueue
from crawler.core_carrier.items import (
    MblItem, BaseCarrierItem, LocationItem, VesselItem, ContainerItem, ContainerStatusItem, ExportErrorData, DebugItem)
from crawler.core_carrier.exceptions import (
    CarrierResponseFormatError, BaseCarrierError, SuspiciousOperationError, CarrierInvalidSearchNoError
)
from crawler.extractors.selector_finder import BaseMatchRule, find_selector_from
from crawler.extractors.table_cell_extractors import BaseTableCellExtractor
from crawler.extractors.table_extractors import BaseTableLocator, HeaderMismatchError, TableExtractor

WHLC_BASE_URL = 'https://tw.wanhai.com'


class CarrierWhlcSpider(BaseCarrierSpider):
    name = 'carrier_whlc'

    custom_settings = {
        **CARRIER_DEFAULT_SETTINGS,
        **DISABLE_DUPLICATE_REQUEST_FILTER,
    }

    def __init__(self, *args, **kwargs):
        super(CarrierWhlcSpider, self).__init__(*args, **kwargs)

        bill_rules = [
            BillRoutingRule(search_type=SHIPMENT_TYPE_MBL)
        ]

        booking_rules = [
            BillRoutingRule(search_type=SHIPMENT_TYPE_BOOKING)
        ]

        if self.mbl_no:
            self._rule_manager = RuleManager(rules=bill_rules)
            self.search_no = self.mbl_no
        else:
            self._rule_manager = RuleManager(rules=booking_rules)
            self.search_no = self.booking_no
        self._request_queue = RequestOptionQueue()

    def start(self):
        request_option = BillRoutingRule.build_request_option(search_no=self.search_no)
        yield self._build_request_by(option=request_option)

    def parse(self, response):
        yield DebugItem(info={'meta': dict(response.meta)})

        routing_rule = self._rule_manager.get_rule_by_response(response=response)

        save_name = routing_rule.get_save_name(response=response)
        self._saver.save(to=save_name, text=response.text)

        for result in routing_rule.handle(response=response):
            if isinstance(result, BaseCarrierItem):
                yield result
            elif isinstance(result, RequestOption):
                self._request_queue.add_request(result)
            else:
                raise RuntimeError()

        if not self._request_queue.is_empty():
            request_option = self._request_queue.get_next_request()
            yield self._build_request_by(option=request_option)

    def _build_request_by(self, option: RequestOption):
        meta = {
            RuleManager.META_CARRIER_CORE_RULE_NAME: option.rule_name,
            **option.meta,
        }

        if option.method == RequestOption.METHOD_POST_BODY:
            return scrapy.Request(
                url=option.url,
                headers=option.headers,
                meta=meta,
                callback=self.parse,
                method='POST',
                body=option.body,
            )
        elif option.method == RequestOption.METHOD_GET:
            return scrapy.Request(
                url=option.url,
                headers=option.headers,
                cookies=option.cookies,
                meta=meta,
            )
        else:
            raise SuspiciousOperationError(msg=f'Unexpected request method: `{option.method}`')

# -------------------------------------------------------------------------------


class CarrierIpBlockError(BaseCarrierError):
    status = CARRIER_RESULT_STATUS_FATAL

    def build_error_data(self):
        return ExportErrorData(status=self.status, detail='<ip-block-error>')


class BillRoutingRule(BaseRoutingRule):
    name = 'BILL'

    def __init__(self, search_type):
        self._search_type = search_type
        self._container_patt = re.compile(r'^(?P<container_no>\w+)')

    @classmethod
    def build_request_option(cls, search_no):
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=f'https://google.com',
            meta={'search_no': search_no},
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.html'

    def handle(self, response):
        search_no = response.meta['search_no']
        driver = WhlcDriver()
        cookies = driver.get_cookies_dict_from_main_page()
        driver.search(search_no=search_no, search_type=self._search_type)

        response_selector = Selector(text=driver.get_page_source())
        if self._is_search_no_invalid(response=response_selector):
            raise CarrierInvalidSearchNoError(search_type=self._search_type)

        container_nos = self._extract_container_nos(response_selector)

        yield MblItem(mbl_no=search_no)

        for idx in range(len(container_nos)):
            container_no = container_nos[idx]

            yield ContainerItem(
                container_key=container_no,
                container_no=container_no,
            )

            # detail page -- extract vessel
            driver.go_detail_page(idx+2)
            detail_selector = Selector(text=driver.get_page_source())
            vessel_items = self._make_vessel_items(response=detail_selector)
            for item in vessel_items:
                yield item

            driver.close()
            driver.switch_to_last()

            # history page
            driver.go_history_page(idx+2)
            history_selector = Selector(text=driver.get_page_source())
            container_status_items = self._make_container_status_items(
                response=history_selector, container_no=container_no)

            for item in container_status_items:
                yield item

            driver.close()
            driver.switch_to_last()

    @staticmethod
    def _is_search_no_invalid(response):
        if response.css('input#q_ref_no1'):
            return True
        return False

    def _extract_container_nos(self, response: scrapy.Selector) -> List:
        try:
            table_selector = response.css('table.tbl-list')[0]
        except IndexError as err:
            print(response.css('table.tbl-list').get())
            raise err

        table_locator = ContainerListTableLocator()
        table_locator.parse(table=table_selector)
        table = TableExtractor(table_locator=table_locator)
        return_list = []
        for left in table_locator.iter_left_headers():
            container_no_text = table.extract_cell('櫃號', left)
            container_no = self._parse_container_no_from(text=container_no_text)

            return_list.append(container_no)

        return return_list

    def _parse_container_no_from(self, text):
        if not text:
            raise CarrierResponseFormatError('container_no not found')

        m = self._container_patt.match(text)
        if not m:
            raise CarrierResponseFormatError('container_no not match')

        return m.group('container_no')

    @classmethod
    def _make_vessel_items(cls, response: Selector):
        date_information = cls._extract_date_information(response=response)

        return [
            VesselItem(
                vessel_key=f"{date_information['pol_vessel']} / {date_information['pol_voyage']}",
                vessel=date_information['pol_vessel'],
                voyage=date_information['pol_voyage'],
                pol=LocationItem(un_lo_code=date_information['pol_un_lo_code']),
                etd=date_information['pol_etd'],
            ),
            VesselItem(
                vessel_key=f"{date_information['pod_vessel']} / {date_information['pod_voyage']}",
                vessel=date_information['pod_vessel'],
                voyage=date_information['pod_voyage'],
                pod=LocationItem(un_lo_code=date_information['pod_un_lo_code']),
                eta=date_information['pod_eta'],
            ),
        ]

    @staticmethod
    def _extract_date_information(response) -> Dict:
        pattern = re.compile(r'^(?P<vessel>[^/]+) / (?P<voyage>[^/]+)$')

        match_rule = NameOnTableMatchRule(name='2. 出發日期 / 抵達日期 訊息')

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

        pol_vessel_voyage = location_table.extract_cell(top=vessel_voyage_index, left='裝貨港')
        pol_m = pattern.match(pol_vessel_voyage)
        pol_vessel = pol_m.group('vessel')
        pol_voyage = pol_m.group('voyage')

        pod_vessel_voyage = location_table.extract_cell(top=vessel_voyage_index, left='卸貨港')
        pod_m = pattern.match(pod_vessel_voyage)
        pod_vessel = pod_m.group('vessel')
        pod_voyage = pod_m.group('voyage')

        return {
            'pol_un_lo_code': location_table.extract_cell(top=un_lo_code_index, left='裝貨港'),
            'pod_un_lo_code': location_table.extract_cell(top=un_lo_code_index, left='卸貨港'),
            'pol_vessel': pol_vessel,
            'pol_voyage': pol_voyage,
            'pod_vessel': pod_vessel,
            'pod_voyage': pod_voyage,
            'pod_eta': date_table.extract_cell(top=date_index, left='抵達日期'),
            'pol_etd': date_table.extract_cell(top=date_index, left='出發日期'),
        }

    @classmethod
    def _make_container_status_items(cls, response, container_no):
        container_status_list = cls._extract_container_status(response=response)

        container_statuses = []
        for container_status in container_status_list:
            container_statuses.append(
                ContainerStatusItem(
                    container_key=container_no,
                    local_date_time=container_status['local_date_time'],
                    description=container_status['description'],
                    location=LocationItem(name=container_status['location_name']),
                )
            )
        return container_statuses

    @staticmethod
    def _extract_container_status(response) -> List:
        table_selector = response.css('table.tbl-list')

        if not table_selector:
            raise CarrierResponseFormatError(reason='container status table not found')

        table_locator = ContainerStatusTableLocator()
        table_locator.parse(table=table_selector)
        table = TableExtractor(table_locator=table_locator)

        return_list = []
        for left in table_locator.iter_left_headers():
            description = table.extract_cell(top='狀態', left=left, extractor=DescriptionTdExtractor())
            local_date_time = table.extract_cell(top='日期', left=left, extractor=LocalDateTimeTdExtractor())
            location_name = table.extract_cell(top='櫃場名稱', left=left, extractor=LocationNameTdExtractor())

            return_list.append({
                'local_date_time': local_date_time,
                'description': description,
                'location_name': location_name,
            })

        return return_list


# -------------------------------------------------------------------------------


class BookingRoutingRule(BaseRoutingRule):
    name = 'BOOKING'

    def __init__(self, search_type):
        self._search_type = search_type
        self._container_patt = re.compile(r'^(?P<container_no>\w+)')

    @classmethod
    def build_request_option(cls, search_no):
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=f'https://google.com',
            meta={'search_no': search_no},
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.html'

    def handle(self, response):
        search_no = response.meta['search_no']
        driver = WhlcDriver()
        cookies = driver.get_cookies_dict_from_main_page()
        driver.search(search_no=search_no, search_type=self._search_type)

        response_selector = Selector(text=driver.get_page_source())
        if self._is_search_no_invalid(response=response_selector):
            raise CarrierInvalidSearchNoError(search_type=self._search_type)

        yield MblItem(booking_no=search_no)

        driver.go_detail_page(2)  # only one booking_no to click
        container_nos = self._extract_container_no_and_status_links(response_selector)

        for idx in range(len(container_nos)):
            container_no = container_nos[idx]

            yield ContainerItem(
                container_key=container_no,
                container_no=container_no,
            )

            # extract vessel
            detail_selector = Selector(text=driver.get_page_source())
            vessel_items = self._make_vessel_items(response=detail_selector)
            for item in vessel_items:
                yield item

            driver.close()
            driver.switch_to_last()

            # history page
            driver.go_history_page(idx+2)
            history_selector = Selector(text=driver.get_page_source())
            container_status_items = self._make_container_status_items(
                response=history_selector, container_no=container_no)

            for item in container_status_items:
                yield item

            driver.close()
            driver.switch_to_last()

    @staticmethod
    def _is_search_no_invalid(response):
        if response.css('input#q_ref_no1'):
            return True
        return False

    def _extract_container_no_and_status_links(self, response: scrapy.Selector) -> List:
        tables = response.css('table.tbl-list')
        rule = TableTitleExistRule(title='櫃號')
        table = find_selector_from(selectors=tables, rule=rule)

        table_locator = ContainerListTableLocator()
        table_locator.parse(table=table)
        table_extractor = TableExtractor(table_locator=table_locator)
        return_list = []
        for left in table_locator.iter_left_headers():
            container_no_text = table_extractor.extract_cell('櫃號', left)
            container_no = self._parse_container_no_from(text=container_no_text)

            return_list.append(container_no)

        return return_list

    def _parse_container_no_from(self, text):
        if not text:
            raise CarrierResponseFormatError('container_no not found')

        m = self._container_patt.match(text)
        if not m:
            raise CarrierResponseFormatError('container_no not match')

        return m.group('container_no')

    @classmethod
    def _make_vessel_items(cls, response: Selector):
        date_information = cls._extract_date_information(response=response)

        return [
            VesselItem(
                vessel_key=f"{date_information['pol_vessel']} / {date_information['pol_voyage']}",
                vessel=date_information['pol_vessel'],
                voyage=date_information['pol_voyage'],
                pol=LocationItem(un_lo_code=date_information['pol_un_lo_code']),
                etd=date_information['pol_etd'],
            ),
            VesselItem(
                vessel_key=f"{date_information['pod_vessel']} / {date_information['pod_voyage']}",
                vessel=date_information['pod_vessel'],
                voyage=date_information['pod_voyage'],
                pod=LocationItem(un_lo_code=date_information['pod_un_lo_code']),
                eta=date_information['pod_eta'],
            ),
        ]

    @staticmethod
    def _extract_date_information(response) -> Dict:
        pattern = re.compile(r'^(?P<vessel>[^/]+) / (?P<voyage>[^/]+)$')

        match_rule = NameOnTableMatchRule(name='2. 出發日期 / 抵達日期 訊息')

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

        pol_vessel_voyage = location_table.extract_cell(top=vessel_voyage_index, left='裝貨港')
        pol_m = pattern.match(pol_vessel_voyage)
        pol_vessel = pol_m.group('vessel')
        pol_voyage = pol_m.group('voyage')

        pod_vessel_voyage = location_table.extract_cell(top=vessel_voyage_index, left='卸貨港')
        pod_m = pattern.match(pod_vessel_voyage)
        pod_vessel = pod_m.group('vessel')
        pod_voyage = pod_m.group('voyage')

        return {
            'pol_un_lo_code': location_table.extract_cell(top=un_lo_code_index, left='裝貨港'),
            'pod_un_lo_code': location_table.extract_cell(top=un_lo_code_index, left='卸貨港'),
            'pol_vessel': pol_vessel,
            'pol_voyage': pol_voyage,
            'pod_vessel': pod_vessel,
            'pod_voyage': pod_voyage,
            'pod_eta': date_table.extract_cell(top=date_index, left='抵達日期'),
            'pol_etd': date_table.extract_cell(top=date_index, left='出發日期'),
        }

    @classmethod
    def _make_container_status_items(cls, response, container_no):
        container_status_list = cls._extract_container_status(response=response)

        container_statuses = []
        for container_status in container_status_list:
            container_statuses.append(
                ContainerStatusItem(
                    container_key=container_no,
                    local_date_time=container_status['local_date_time'],
                    description=container_status['description'],
                    location=LocationItem(name=container_status['location_name']),
                )
            )
        return container_statuses

    @staticmethod
    def _extract_container_status(response) -> List:
        table_selector = response.css('table.tbl-list')

        if not table_selector:
            raise CarrierResponseFormatError(reason='container status table not found')

        table_locator = ContainerStatusTableLocator()
        table_locator.parse(table=table_selector)
        table = TableExtractor(table_locator=table_locator)

        return_list = []
        for left in table_locator.iter_left_headers():
            description = table.extract_cell(top='狀態', left=left, extractor=DescriptionTdExtractor())
            local_date_time = table.extract_cell(top='日期', left=left, extractor=LocalDateTimeTdExtractor())
            location_name = table.extract_cell(top='櫃場名稱', left=left, extractor=LocationNameTdExtractor())

            return_list.append({
                'local_date_time': local_date_time,
                'description': description,
                'location_name': location_name,
            })

        return return_list


class WhlcDriver:
    def __init__(self):
        # Firefox
        useragent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11.1; rv:78.0) Gecko/20100101 Firefox/78.0'
        profile = webdriver.FirefoxProfile()
        profile.set_preference("general.useragent.override", useragent)
        options = webdriver.FirefoxOptions()
        options.set_preference("dom.webnotifications.serviceworker.enabled", False)
        options.set_preference("dom.webnotifications.enabled", False)
        options.add_argument('--headless')

        self._driver = webdriver.Firefox(firefox_profile=profile, options=options, service_log_path='/dev/null')

        self._type_select_text_map = {
            SHIPMENT_TYPE_MBL: '提單號碼',
            SHIPMENT_TYPE_BOOKING: '訂艙號碼',
        }

        # Google Chrome
        # options = webdriver.ChromeOptions()
        # options.add_argument('--disable-extensions')
        # options.add_argument('--disable-notifications')
        # options.add_argument('--headless')
        # options.add_argument("--enable-javascript")
        # options.add_argument('--disable-gpu')
        # options.add_argument(f'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.79 Safari/537.36')
        # options.add_argument('--disable-dev-shm-usage')
        # options.add_argument('--no-sandbox')
        # options.add_argument('--window-size=1920,1080')
        # options.add_experimental_option('excludeSwitches', ['enable-automation'])
        # options.add_experimental_option('useAutomationExtension', False)
        # options.add_argument('--disable-blink-features=AutomationControlled')
        #
        # self._driver = webdriver.Chrome(chrome_options=options)
        # self._driver.execute_script("Object.defineProperty(window, 'outerWidth', {value: 1920+800})")
        # self._driver.execute_script("Object.defineProperty(window, 'outerHeight', {value: 1080+600})")
        #
        # print('hihi', self._driver.execute_script("return [window.outerWidth, window.outerHeight];"))
        # print('soso', self._driver.execute_script("return [window.innerWidth, window.innerHeight];"))
        #
        # # undefine navigator.webdriver
        # script = "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        # self._driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {'source': script})
        # print('soso', self._driver.execute_script("return navigator.webdriver;"))

    def get_cookies_dict_from_main_page(self):

        self._driver.get(f'{WHLC_BASE_URL}')
        time.sleep(5)
        # self._driver.get_screenshot_as_file("output-1.png")
        cookies = self._driver.get_cookies()

        return self._transformat_to_dict(cookies=cookies)

    def get_view_state(self):
        view_state_elem = self._driver.find_element_by_css_selector('input[name="javax.faces.ViewState"]')
        view_state = view_state_elem.get_attribute('value')
        return view_state

    def close(self):
        self._driver.close()

    def get_page_source(self):
        return self._driver.page_source

    def search(self, search_no, search_type):
        select_text = self._type_select_text_map[search_type]

        self._driver.find_element_by_xpath(f"//*[@id='cargoType']/option[text()='{select_text}']").click()
        time.sleep(1)
        input_ele = self._driver.find_element_by_xpath('//*[@id="q_ref_no1"]')
        input_ele.send_keys(search_no)
        time.sleep(3)
        self._driver.find_element_by_xpath('//*[@id="quick_ctnr_query"]').click()
        time.sleep(5)
        self._driver.switch_to.window(self._driver.window_handles[-1])

    def go_detail_page(self, idx: int):
        loader = self._driver.find_element_by_css_selector('div#loader')
        print('test loader', loader.get_attribute('outerHTML'))
        self._driver.find_element_by_xpath(f'//*[@id="cargoTrackListBean"]/table/tbody/tr[{idx}]/td[1]/u').click()
        time.sleep(5)
        self._driver.switch_to.window(self._driver.window_handles[-1])

    def go_history_page(self, idx: int):
        self._driver.find_element_by_xpath(f'//*[@id="cargoTrackListBean"]/table/tbody/tr[{idx}]/td[11]/u').click()
        time.sleep(5)
        self._driver.switch_to.window(self._driver.window_handles[-1])

    def switch_to_last(self):
        self._driver.switch_to.window(self._driver.window_handles[-1])
        time.sleep(1)

    @staticmethod
    def _transformat_to_dict(cookies: List[Dict]) -> Dict:
        return_cookies = {}

        for d in cookies:
            return_cookies[d['name']] = d['value']

        return return_cookies


# -------------------------------------------------------------------------------


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


class DescriptionTdExtractor(BaseTableCellExtractor):

    def extract(self, cell: Selector) -> str:
        td_text = cell.css('::text').get()
        td_text = td_text.replace('\\n', '')
        td_text = ' '.join(td_text.split())
        return td_text.strip()


class LocalDateTimeTdExtractor(BaseTableCellExtractor):

    def extract(self, cell: Selector) -> str:
        td_text = cell.css('::text').get()
        td_text = td_text.replace('\\n', '')
        return td_text.strip()


class LocationNameTdExtractor(BaseTableCellExtractor):

    def extract(self, cell: Selector) -> str:
        td_text = cell.css('::text').get()
        td_text = td_text.replace('\\n', '')
        td_text = td_text.replace('\\t', '')
        return td_text.strip()


class NameOnTableMatchRule(BaseMatchRule):
    TABLE_NAME_QUERY = 'tr td a::text'

    def __init__(self, name: str):
        self.name = name

    def check(self, selector: scrapy.Selector) -> bool:
        table_name = selector.css(self.TABLE_NAME_QUERY).get()

        if not isinstance(table_name, str):
            return False

        return table_name.strip() == self.name


class TableTitleExistRule(BaseMatchRule):
    def __init__(self, title: str):
        self.title = title

    def check(self, selector: scrapy.Selector) -> bool:
        raw_th_texts = selector.css('th::text').getall()
        th_texts = [t.strip() for t in raw_th_texts]

        return self.title in th_texts