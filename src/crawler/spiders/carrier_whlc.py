import re
import time
from urllib.parse import urlencode
from six.moves.urllib.parse import urljoin
from typing import List, Dict

import scrapy
import requests
from scrapy import Selector
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.keys import Keys

from crawler.core_carrier.base import CARRIER_RESULT_STATUS_FATAL
from crawler.core_carrier.base_spiders import (
    BaseCarrierSpider, CARRIER_DEFAULT_SETTINGS, DISABLE_DUPLICATE_REQUEST_FILTER)
from crawler.core_carrier.request_helpers import RequestOption
from crawler.core_carrier.rules import RuleManager, BaseRoutingRule, RequestOptionQueue
from crawler.core_carrier.items import (
    BaseCarrierItem, LocationItem, VesselItem, ContainerItem, ContainerStatusItem, ExportErrorData, DebugItem)
from crawler.core_carrier.exceptions import CarrierResponseFormatError, CarrierInvalidMblNoError, BaseCarrierError, \
    SuspiciousOperationError
from crawler.extractors.selector_finder import BaseMatchRule, find_selector_from
from crawler.extractors.table_cell_extractors import BaseTableCellExtractor
from crawler.extractors.table_extractors import BaseTableLocator, HeaderMismatchError, TableExtractor

WHLC_BASE_URL = 'https://tw.wanhai.com'
COOKIES_RETRY_LIMIT = 3


class CarrierWhlcSpider(BaseCarrierSpider):
    name = 'carrier_whlc'

    custom_settings = {
        **CARRIER_DEFAULT_SETTINGS,
        **DISABLE_DUPLICATE_REQUEST_FILTER,
    }

    def __init__(self, *args, **kwargs):
        super(CarrierWhlcSpider, self).__init__(*args, **kwargs)

        rules = [
            SeleniumRule()
            # CookiesRoutingRule(),
            # RefreshCookieRule(),
            # ListRoutingRule(),
            # DetailRoutingRule(),
            # HistoryRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)
        self._request_queue = RequestOptionQueue()

    def start(self):
        request_option = SeleniumRule.build_request_option(mbl_no=self.mbl_no)
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


class SeleniumRule(BaseCarrierError):
    name = 'SELENIUM'

    def __init__(self):
        self._container_patt = re.compile(r'^(?P<container_no>\w+)')
        self._j_idt_patt = re.compile(r"'(?P<j_idt>j_idt[^,]+)':'(?P=j_idt)'")

    @classmethod
    def build_request_option(cls, mbl_no):
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=f'https://google.com',
            meta={'mbl_no': mbl_no},
        )

    def handle(self, response):
        mbl_no = response.meta['mbl_no']
        driver = WhlcDriver()
        cookies = driver.get_cookies_dict_from_main_page()
        driver.search_mbl(mbl_no)

        response_selector = Selector(text=driver.get_page_source())
        container_list = self._extract_container_info(response_selector)

        for idx in range(len(container_list)):
            container_no = container_list[idx]['container_no']

            yield ContainerItem(
                container_key=container_no,
                container_no=container_no,
            )

            # detail page
            driver.go_detail_page(idx+2)
            detail_selector = Selector(text=driver.get_page_source())
            date_information = self._extract_date_information(detail_selector)

            yield VesselItem(
                vessel_key=f"{date_information['pol_vessel']} / {date_information['pol_voyage']}",
                vessel=date_information['pol_vessel'],
                voyage=date_information['pol_voyage'],
                pol=LocationItem(un_lo_code=date_information['pol_un_lo_code']),
                etd=date_information['pol_etd'],
            )

            yield VesselItem(
                vessel_key=f"{date_information['pod_vessel']} / {date_information['pod_voyage']}",
                vessel=date_information['pod_vessel'],
                voyage=date_information['pod_voyage'],
                pod=LocationItem(un_lo_code=date_information['pod_un_lo_code']),
                eta=date_information['pod_eta'],
            )

            driver.close()
            driver.switch_to_last()

            # history page
            driver.go_history_page(idx+2)
            history_selector = Selector(text=driver.get_page_source())
            container_status_list = self._extract_container_status(history_selector)

            for container_status in container_status_list:
                yield ContainerStatusItem(
                    container_key=container_no,
                    local_date_time=container_status['local_date_time'],
                    description=container_status['description'],
                    location=LocationItem(name=container_status['location_name']),
                )

            driver.close()
            driver.switch_to_last()

    def get_save_name(self, response) -> str:
        return f'{self.name}.html'

    def _extract_container_info(self, response: scrapy.Selector) -> List:
        table_selector = response.css('table.tbl-list')[0]
        table_locator = ContainerListTableLocator()
        table_locator.parse(table=table_selector)
        table = TableExtractor(table_locator=table_locator)
        return_list = []
        for left in table_locator.iter_left_headers():
            container_no_text = table.extract_cell('櫃號', left)
            container_no = self._parse_container_no_from(text=container_no_text)

            detail_j_idt_text = table.extract_cell('明細查詢', left, JidtTdExtractor())
            detail_j_idt = self._parse_detail_j_idt_from(text=detail_j_idt_text)

            history_j_idt_text = table.extract_cell('歷史動態', left, JidtTdExtractor())
            history_j_idt = self._parse_history_j_idt_from(text=history_j_idt_text)

            return_list.append({
                'container_no': container_no,
                'detail_j_idt': detail_j_idt,
                'history_j_idt': history_j_idt,
            })

        return return_list

    def _parse_container_no_from(self, text):
        if not text:
            raise CarrierResponseFormatError('container_no not found')

        m = self._container_patt.match(text)
        if not m:
            raise CarrierResponseFormatError('container_no not match')

        return m.group('container_no')

    def _parse_detail_j_idt_from(self, text: str) -> str:
        if not text:
            return ''

        m = self._j_idt_patt.search(text)
        if not m:
            raise CarrierResponseFormatError('detail_j_idt not match')

        return m.group('j_idt')

    def _parse_history_j_idt_from(self, text: str) -> str:
        if not text:
            return ''

        m = self._j_idt_patt.search(text)
        if not m:
            raise CarrierResponseFormatError('History_j_idt not match')

        return m.group('j_idt')

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
        options = webdriver.ChromeOptions()
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-notifications')
        options.add_argument('--headless')
        options.add_argument("--enable-javascript")
        options.add_argument('--disable-gpu')
        options.add_argument(f'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.79 Safari/537.36')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument('--window-size=1920,1080')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)

        self._driver = webdriver.Chrome(chrome_options=options)

        # undefine navigator.webdriver
        script = "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        self._driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {'source': script})

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

    def search_mbl(self, mbl_no):
        self._driver.find_element_by_xpath("//*[@id='cargoType']/option[text()='提單號碼']").click()
        time.sleep(1)
        input_ele = self._driver.find_element_by_xpath('//*[@id="q_ref_no1"]')
        input_ele.send_keys(mbl_no)
        time.sleep(3)
        self._driver.find_element_by_xpath('//*[@id="quick_ctnr_query"]').click()
        time.sleep(5)
        self._driver.switch_to.window(self._driver.window_handles[-1])

    def go_detail_page(self, idx: int):
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

class CookiesRoutingRule(BaseRoutingRule):
    name = 'COOKIES'

    def __init__(self):
        self._retry_count = 0

    @classmethod
    def build_request_option(cls, mbl_no) -> RequestOption:
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=f'{WHLC_BASE_URL}/views/Main.xhtml',
            meta={'mbl_no': mbl_no},
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.html'

    def handle(self, response):
        mbl_no = response.meta['mbl_no']

        driver = WhlcDriver()
        cookies = driver.get_cookies_dict_from_main_page()

        view_state = driver.get_view_state()
        if view_state:
            driver.close()
            yield RefreshCookieRule.build_request_option('ListRoutingRule', mbl_no, view_state, cookies=cookies)
            # yield ListRoutingRule.build_request_option(mbl_no, view_state, cookies=cookies)
        else:
            driver.close()
            raise CarrierIpBlockError()

    @staticmethod
    def _check(cookies: Dict) -> bool:
        # check visid_incap_2465608 & incap_ses_932_2465608 format exist

        visid_incap_existence, incap_ses_existence = False, False
        for k, v in cookies.items():
            if 'visid_incap' in k:
                visid_incap_existence = True
            elif 'incap_ses' in k:
                incap_ses_existence = True

        return visid_incap_existence and incap_ses_existence

    @staticmethod
    def _check_cookies(response):
        cookies = {}

        for cookie in response.headers.getlist('Set-Cookie'):
            item = cookie.decode('utf-8').split(';')[0]
            key, value = item.split('=', 1)
            cookies[key] = value

        return bool(cookies)

    @staticmethod
    def _extract_view_state(response: scrapy.Selector) -> str:
        return response.css('input[name="javax.faces.ViewState"]::attr(value)').get()


class RefreshCookieRule(BaseRoutingRule):
    name = 'REFRESH'

    @classmethod
    def build_request_option(cls, next_rule: str, mbl_no: str, view_state, cookies):
        if next_rule == 'ListRoutingRule':
            form_data = {
                'cargoTrackListBean': 'cargoTrackListBean',
                'cargoType': '2',
                'q_ref_no1': mbl_no,
                'quick_ctnr_query': '查詢',
                'javax.faces.ViewState': view_state,
            }

            headers = {
                'cache-control': 'max-age=0',
                'upgrade-insecure-requests': '1',
                'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_1_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'sec-fetch-site': 'same-origin',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-user': '?1',
                'sec-fetch-dest': 'document',
                'sec-ch-ua': '"Google Chrome";v="87", " Not;A Brand";v="99", "Chromium";v="87"',
                'sec-ch-ua-mobile': '?0',
                'referer': 'https://tw.wanhai.com/views/Main.xhtml',
                'accept-language': 'en-US,en;q=0.9',
                'cookie': cls._get_cookie_str(cookies),
            }

            return RequestOption(
                rule_name=cls.name,
                method=RequestOption.METHOD_POST_BODY,
                url=f'{WHLC_BASE_URL}/views/quick/cargo_tracking.xhtml',
                cookies=cookies,
                headers=headers,
                body=urlencode(query=form_data),
                meta={'mbl_no': mbl_no, 'cookies': cookies, 'headers': headers},
            )

    def handle(self, response):

        mbl_no = response.meta['mbl_no']
        cookies = response.meta['cookies']

        cookie_bytes = response.headers.getlist('Set-Cookie')

        for cookie_byte in cookie_bytes:
            cookie_text = cookie_byte.decode('utf-8')
            key, value = self._parse_cookie(cookie_text=cookie_text)
            cookies[key] = value

        yield ListRoutingRule.build_request_option(mbl_no=mbl_no, cookies=cookies)

    @staticmethod
    def _get_cookie_str(cookies: Dict):
        cookies_str = ''
        for key, value in cookies.items():
            cookies_str += f'{key}={value}; '

    def _parse_cookie(self, cookie_text):
        """
        Sample 1: `TS01a3c52a=01541c804a3dfa684516e96cae7a588b5eea6236b8843ebfc7882ca3e47063c4b3fddc7cc2e58145e71bee297`
                  `3391cc28597744f23343d7d2544d27a2ce90ca4b356ffb78f5; Path=/`
        Sample 2: `TSff5ac71e_27=081ecde62cab2000428f3620d78d07ee66ace44f9dc6c6feb6bc1bab646fbc7179082123944d1473084a`
                  `f55ddf1120009050da999bcc34164749e3339b930c12ec88cf3b1cfb6cd3b77b94f5d061834e;Path=/`
        """
        cookies_pattern = re.compile(r'^(?P<key>[^=]+)=(?P<value>[^;]+);.+$')
        match = cookies_pattern.match(cookie_text)
        if not match:
            CarrierResponseFormatError(f'Unknown cookie format: `{cookie_text}`')

        return match.group('key'), match.group('value')


# -------------------------------------------------------------------------------

class ListRoutingRule(BaseRoutingRule):
    name = 'LIST'

    def __init__(self):
        self._container_patt = re.compile(r'^(?P<container_no>\w+)')
        self._j_idt_patt = re.compile(r"'(?P<j_idt>j_idt[^,]+)':'(?P=j_idt)'")

    @classmethod
    def build_request_option(cls, mbl_no, cookies) -> RequestOption:
        cookies_str = ''
        for key, value in cookies.items():
            cookies_str += f'{key}={value}; '

        headers = {
            'cache-control': 'max-age=0',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_1_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-user': '?1',
            'sec-fetch-dest': 'document',
            'sec-ch-ua': '"Google Chrome";v="87", " Not;A Brand";v="99", "Chromium";v="87"',
            'sec-ch-ua-mobile': '?0',
            'referer': 'https://tw.wanhai.com/views/Main.xhtml',
            'accept-language': 'en-US,en;q=0.9',
            'cookie': cookies_str,
        }

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=f'{WHLC_BASE_URL}/views/cargoTrack/CargoTrackList.xhtml?file_num=65580&top_file_num=64735&parent_id=64738',
            cookies=cookies,
            headers=headers,
            meta={'mbl_no': mbl_no, 'cookies': cookies},
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.html'

    def handle(self, response):
        mbl_no = response.meta['mbl_no']
        cookies = response.meta['cookies']

        self._check_response(response)

        view_state = self._extract_view_state(response=response)

        container_list = self._extract_container_info(response=response)
        for container in container_list:
            container_no = container['container_no']

            yield ContainerItem(
                container_key=container_no,
                container_no=container_no,
            )

            detail_j_idt = container['detail_j_idt']
            if detail_j_idt:
                yield DetailRoutingRule.build_request_option(mbl_no, container_no, detail_j_idt, view_state, cookies)

            history_j_idt = container['history_j_idt']
            if history_j_idt:
                yield HistoryRoutingRule.build_request_option(mbl_no, container_no, history_j_idt, view_state, cookies)

    @staticmethod
    def _check_response(response):
        if response.css('form[action="/views/AlertMsgPage.xhtml"]'):
            raise CarrierInvalidMblNoError()

    @staticmethod
    def _extract_view_state(response: scrapy.Selector) -> str:
        return response.css('input[name="javax.faces.ViewState"]::attr(value)').get()

    def _extract_container_info(self, response: scrapy.Selector) -> List:
        table_selector = response.css('table.tbl-list')[0]
        table_locator = ContainerListTableLocator()
        table_locator.parse(table=table_selector)
        table = TableExtractor(table_locator=table_locator)
        return_list = []
        for left in table_locator.iter_left_headers():
            container_no_text = table.extract_cell('Ctnr No.', left)
            container_no = self._parse_container_no_from(text=container_no_text)

            detail_j_idt_text = table.extract_cell('More detail', left, JidtTdExtractor())
            detail_j_idt = self._parse_detail_j_idt_from(text=detail_j_idt_text)

            history_j_idt_text = table.extract_cell('More History', left, JidtTdExtractor())
            history_j_idt = self._parse_history_j_idt_from(text=history_j_idt_text)

            return_list.append({
                'container_no': container_no,
                'detail_j_idt': detail_j_idt,
                'history_j_idt': history_j_idt,
            })

        return return_list

    def _parse_container_no_from(self, text):
        if not text:
            raise CarrierResponseFormatError('container_no not found')

        m = self._container_patt.match(text)
        if not m:
            raise CarrierResponseFormatError('container_no not match')

        return m.group('container_no')

    def _parse_detail_j_idt_from(self, text: str) -> str:
        if not text:
            return ''

        m = self._j_idt_patt.search(text)
        if not m:
            raise CarrierResponseFormatError('detail_j_idt not match')

        return m.group('j_idt')

    def _parse_history_j_idt_from(self, text: str) -> str:
        if not text:
            return ''

        m = self._j_idt_patt.search(text)
        if not m:
            raise CarrierResponseFormatError('History_j_idt not match')

        return m.group('j_idt')


class JidtTdExtractor(BaseTableCellExtractor):

    def extract(self, cell: Selector):
        j_idt_text = cell.css('u a::attr(onclick)').get()
        return j_idt_text


# -----------------------------------------------------------------------------


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
    def build_request_option(cls, mbl_no: str, container_no, j_idt, view_state, cookies) -> RequestOption:
        form_data = {
            'cargoTrackListBean': 'cargoTrackListBean',
            'javax.faces.ViewState': view_state,
            j_idt: j_idt,
            'q_bl_no': mbl_no,
            'q_ctnr_no': container_no,
        }

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_POST_FORM,
            url=f'{WHLC_BASE_URL}/views/cargoTrack/CargoTrackList.xhtml',
            form_data=form_data,
            cookies=cookies,
            meta={'container_no': container_no},
        )

    def get_save_name(self, response) -> str:
        container_no = response.meta['container_no']
        return f'{self.name}_{container_no}.html'

    def handle(self, response):
        date_information = self._extract_date_information(response=response)

        yield VesselItem(
            vessel_key=f"{date_information['pol_vessel']} / {date_information['pol_voyage']}",
            vessel=date_information['pol_vessel'],
            voyage=date_information['pol_voyage'],
            pol=LocationItem(un_lo_code=date_information['pol_un_lo_code']),
            etd=date_information['pol_etd'],
        )

        yield VesselItem(
            vessel_key=f"{date_information['pod_vessel']} / {date_information['pod_voyage']}",
            vessel=date_information['pod_vessel'],
            voyage=date_information['pod_voyage'],
            pod=LocationItem(un_lo_code=date_information['pod_un_lo_code']),
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
            'pod_eta': date_table.extract_cell(top=date_index, left='Arrival Date'),
            'pol_etd': date_table.extract_cell(top=date_index, left='Departure Date'),
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
    def build_request_option(cls, mbl_no: str, container_no, j_idt, view_state, cookies) -> RequestOption:
        form_data = {
            'cargoTrackListBean': 'cargoTrackListBean',
            'javax.faces.ViewState': view_state,
            j_idt: j_idt,
            'q_bl_no': mbl_no,
            'q_ctnr_no': container_no,
        }

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_POST_FORM,
            url=f'{WHLC_BASE_URL}/views/cargoTrack/CargoTrackList.xhtml',
            form_data=form_data,
            cookies=cookies,
            meta={
                'container_key': container_no,
            },
        )

    def get_save_name(self, response) -> str:
        container_key = response.meta['container_key']
        return f'{self.name}_{container_key}.html'

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
        table_selector = response.css('table.tbl-list')

        if not table_selector:
            raise CarrierResponseFormatError(reason='container status table not found')

        table_locator = ContainerStatusTableLocator()
        table_locator.parse(table=table_selector)
        table = TableExtractor(table_locator=table_locator)

        return_list = []
        for left in table_locator.iter_left_headers():

            description = table.extract_cell(top='Status Name', left=left, extractor=DescriptionTdExtractor())
            local_date_time = table.extract_cell(top='Ctnr Date', left=left, extractor=LocalDateTimeTdExtractor())
            location_name = table.extract_cell(top='Ctnr Depot Name', left=left, extractor=LocationNameTdExtractor())

            return_list.append({
                'local_date_time': local_date_time,
                'description': description,
                'location_name': location_name,
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
