import random
import re
import time
from queue import Queue
from typing import Dict, List

import scrapy
from scrapy import Selector
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from urllib3.exceptions import ReadTimeoutError

from crawler.core_carrier.base import CARRIER_RESULT_STATUS_ERROR
from crawler.core_carrier.base_spiders import BaseCarrierSpider
from crawler.core_carrier.request_helpers import ProxyManager, RequestOption
from crawler.core_carrier.rules import RuleManager, BaseRoutingRule
from crawler.core_carrier.items import (
    BaseCarrierItem, MblItem, LocationItem, ContainerItem, ContainerStatusItem, DebugItem,
    ExportErrorData)
from crawler.core_carrier.exceptions import CarrierResponseFormatError, CarrierInvalidMblNoError, ProxyMaxRetryError, \
    BaseCarrierError, AcceptLoadWebsiteTimeOutError
from crawler.extractors.selector_finder import CssQueryTextStartswithMatchRule, find_selector_from
from crawler.extractors.table_extractors import BaseTableLocator, HeaderMismatchError, TableExtractor
from crawler.extractors.table_cell_extractors import BaseTableCellExtractor, FirstTextTdExtractor


BASE_URL = 'http://moc.oocl.com'


class ForceRestart:
    pass


class CarrierOoluSpider(BaseCarrierSpider):
    name = 'carrier_oolu'

    def __init__(self, *args, **kwargs):
        super(CarrierOoluSpider, self).__init__(*args, **kwargs)
        # cookiejar ref: https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#std:reqmeta-cookiejar
        self._cookiejar_id = 0
        self._queue = Queue()
        self._driver = OoluDriver()

        rules = [
            CargoTrackingRule(self._driver),
            ContainerStatusRule(self._driver),
        ]

        self._rule_manager = RuleManager(rules=rules)
        self._proxy_manager = ProxyManager(session='oolu', logger=self.logger)

    def start(self):
        yield self._prepare_restart()

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
                proxy_cookie_option = self._add_cookie_jar_into_option(option=proxy_option)
                request = self._build_request_by(option=proxy_cookie_option)
                self._queue.put(request)
            elif isinstance(result, ForceRestart):
                try:
                    request = self._prepare_restart()
                    self._queue.put(request)
                except ProxyMaxRetryError as err:
                    yield err.build_error_data()
            else:
                raise RuntimeError()

        if not self._queue.empty():
            yield self._queue.get()

    def _prepare_restart(self):
        self._proxy_manager.renew_proxy()
        self._cookiejar_id += 1

        option = CargoTrackingRule.build_request_option(
            mbl_no=self.mbl_no,
        )
        return self._build_request_by(option=option)

    def _build_request_by(self, option: RequestOption):
        meta = {
            RuleManager.META_CARRIER_CORE_RULE_NAME: option.rule_name,
            **option.meta,
        }

        if option.method == RequestOption.METHOD_GET:
            return scrapy.Request(
                url=option.url,
                headers=option.headers,
                meta=meta,
                dont_filter=True,
                callback=self.parse,
            )

        elif option.method == RequestOption.METHOD_POST_FORM:
            return scrapy.FormRequest(
                url=option.url,
                headers=option.headers,
                formdata=option.form_data,
                meta=meta,
                dont_filter=True,
                callback=self.parse,
            )

        elif option.method == RequestOption.METHOD_POST_BODY:
            return scrapy.Request(
                method='POST',
                url=option.url,
                headers=option.headers,
                cookies=option.cookies,
                body=option.body,
                meta=meta,
                dont_filter=True,
                callback=self.parse,
            )

        else:
            raise ValueError(f'Invalid option.method [{option.method}]')

    def _add_cookie_jar_into_option(self, option):
        return option.copy_and_extend_by(meta={'cookiejar': self._cookiejar_id})


# -------------------------------------------------------------------------------

class CargoTrackingRule(BaseRoutingRule):
    name = 'CARGO_TRACKING'

    def __init__(self, driver):
        self._driver = driver

    @classmethod
    def build_request_option(cls, mbl_no: str) -> RequestOption:
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url='https://www.google.com',
            meta={
                'mbl_no': mbl_no,
            },
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.html'

    def handle(self, response):
        mbl_no = response.meta['mbl_no']

        try:
            self._driver.goto(url='http://www.oocl.com/eng/Pages/default.aspx')

            self._driver.search_mbl(mbl_no=mbl_no)
        except ReadTimeoutError:
            url = self._driver.get_current_url()
            self._driver.quit()
            raise AcceptLoadWebsiteTimeOutError(url=url)

        response_text = self._driver.get_page_text()
        response = Selector(text=response_text)
        self.check_response(response)

        locator = _PageLocator()
        selector_map = locator.locate_selectors(response=response)

        mbl_no = self._extract_mbl_no(response)
        custom_release_info = self._extract_custom_release_info(selector_map=selector_map)
        routing_info = self._extract_routing_info(selectors_map=selector_map)

        yield MblItem(
            mbl_no=mbl_no,
            vessel=routing_info['vessel'],
            voyage=routing_info['voyage'],
            por=LocationItem(name=routing_info['por']),
            pol=LocationItem(name=routing_info['pol']),
            pod=LocationItem(name=routing_info['pod']),
            etd=routing_info['etd'] or None,
            atd=routing_info['atd'] or None,
            eta=routing_info['eta'] or None,
            ata=routing_info['ata'] or None,
            place_of_deliv=LocationItem(name=routing_info['place_of_deliv']),
            deliv_eta=routing_info['deliv_eta'] or None,
            deliv_ata=routing_info['deliv_ata'] or None,
            final_dest=LocationItem(name=routing_info['final_dest']),
            customs_release_status=custom_release_info['status'] or None,
            customs_release_date=custom_release_info['date'] or None,
        )

        anonymous_token = response.css('input#ANONYMOUS_TOKEN::attr(value)').get()
        jsf_tree_64 = response.css('input[id=jsf_tree_64]::attr(value)').get()
        jsf_state_64 = response.css('input[id=jsf_state_64]::attr(value)').get()

        container_list = self._extract_container_list(selector_map=selector_map)
        for i, container in enumerate(container_list):
            yield ContainerStatusRule.build_request_option(
                container_no=container['container_no'],
                click_element_css=f"a[id='form:link{i}']",
            )

    @staticmethod
    def check_response(response):
        if response.css('span[class=noRecordBold]'):
            raise CarrierInvalidMblNoError()

    def _extract_mbl_no(self, response):
        mbl_no_text = response.css('th.sectionTable::text').get()
        mbl_no = self._parse_mbl_no_text(mbl_no_text)
        return mbl_no

    @staticmethod
    def _parse_mbl_no_text(mbl_no_text):
        # Search Result - Bill of Lading Number  2109051600
        pattern = re.compile(r'^Search\s+Result\s+-\s+Bill\s+of\s+Lading\s+Number\s+(?P<mbl_no>\d+)\s+$')
        match = pattern.match(mbl_no_text)
        if not match:
            raise CarrierResponseFormatError(reason=f'Unknown mbl_no_text: `{mbl_no_text}`')
        return match.group('mbl_no')

    def _extract_custom_release_info(self, selector_map: Dict[str, scrapy.Selector]):
        table = selector_map['summary:main_right_table']

        table_locator = SummaryRightTableLocator()
        table_locator.parse(table)
        table_extractor = TableExtractor(table_locator)
        first_td_extractor = FirstTextTdExtractor()

        if not table_extractor.has_header(top='Inbound Customs Clearance Status:'):
            return {
                'status': '',
                'date': '',
            }

        custom_release_info = table_extractor.extract_cell(
            top='Inbound Customs Clearance Status:', left=None, extractor=first_td_extractor)
        custom_release_status, custom_release_date = self._parse_custom_release_info(custom_release_info)

        return {
            'status': custom_release_status.strip(),
            'date': custom_release_date.strip(),
        }

    @staticmethod
    def _parse_custom_release_info(custom_release_info):
        """
        Sample 1: `Cleared (03 Nov 2019, 16:50 GMT)`
        Sample 2: `Not Applicable`
        Sample 3: ``
        """
        if not custom_release_info:
            return '', ''

        pattern = re.compile(r'^(?P<status>[^(]+)(\s+[(](?P<date>[^)]+)[)])?$')
        match = pattern.match(custom_release_info)
        if not match:
            raise CarrierResponseFormatError(reason=f'Unknown custom_release_info: `{custom_release_info}`')
        return match.group('status').strip(), match.group('date') or ''

    @staticmethod
    def _extract_routing_info(selectors_map: Dict[str, scrapy.Selector]):
        table = selectors_map['detail:routing_table']

        table_locator = RoutingTableLocator()
        table_locator.parse(table=table)
        table_extractor = TableExtractor(table_locator=table_locator)
        span_extractor = FirstTextTdExtractor('span::text')

        # vessel_voyage
        vessel_voyage_extractor = VesselVoyageTdExtractor()
        vessel_voyage = table_extractor.extract_cell(
            top='Vessel Voyage', left=table_locator.LAST_LEFT_HEADER, extractor=vessel_voyage_extractor)

        # por
        por = table_extractor.extract_cell(
            top='Origin', left=table_locator.FIRST_LEFT_HEADER, extractor=span_extractor)

        # pol / pod
        pol_pod_extractor = PolPodTdExtractor()

        pol_info = table_extractor.extract_cell(
            top='Port of Load', left=table_locator.FIRST_LEFT_HEADER, extractor=pol_pod_extractor)
        etd, atd = _get_est_and_actual(status=pol_info['status'], time_str=pol_info['time_str'])

        pod_info = table_extractor.extract_cell(
            top='Port of Discharge', left=table_locator.LAST_LEFT_HEADER, extractor=pol_pod_extractor)
        eta, ata = _get_est_and_actual(status=pod_info['status'], time_str=pod_info['time_str'])

        # place_of_deliv
        deliv_extractor = DelivTdExtractor()
        deliv_info = table_extractor.extract_cell(
            top='Final Destination Hub', left=table_locator.LAST_LEFT_HEADER, extractor=deliv_extractor)
        deliv_eta, deliv_ata = _get_est_and_actual(status=deliv_info['status'], time_str=deliv_info['time_str'])

        # final_dest
        final_dest = table_extractor.extract_cell(
            top='Destination', left=table_locator.LAST_LEFT_HEADER, extractor=span_extractor)

        return {
            'por': por,
            'pol': pol_info['port'],
            'pod': pod_info['port'],
            'place_of_deliv': deliv_info['port'],
            'final_dest': final_dest,
            'etd': etd,
            'atd': atd,
            'eta': eta,
            'ata': ata,
            'deliv_eta': deliv_eta,
            'deliv_ata': deliv_ata,
            'vessel': vessel_voyage['vessel'],
            'voyage': vessel_voyage['voyage'],
        }

    @staticmethod
    def _extract_container_list(selector_map: Dict[str, scrapy.Selector]):
        table = selector_map['summary:container_table']

        container_table_locator = ContainerTableLocator()
        container_table_locator.parse(table=table)
        table_extractor = TableExtractor(table_locator=container_table_locator)

        container_no_list = []
        for left in container_table_locator.iter_left_headers():
            container_no_text = table_extractor.extract_cell('Container Number', left)
            # container_no_text: OOLU843521-8
            container_id, check_no = container_no_text.split('-')
            container_no_list.append({
                'container_id': container_id,
                'container_no': f'{container_id}{check_no}',
            })
        return container_no_list


class OoluDriver:

    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-notifications')
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument('--window-size=1920,1080')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)

        self.driver = webdriver.Chrome(chrome_options=options)

        # undefine navigator.webdriver
        script = "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {'source': script})

    def goto(self, url):
        self.driver.get(url=url)

    def get_current_url(self):
        return self.driver.current_url

    def get_page_text(self):
        return self.driver.page_source

    def find_container_btn_and_click(self, container_btn_css):
        contaienr_btn = self.driver.find_element_by_css_selector(container_btn_css)
        contaienr_btn.click()

    def _click_cookies_and_search(self, mbl_no):
        time.sleep(10)

        cookie_accept_btn = WebDriverWait(self.driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'form > button#btn_cookie_accept'))
        )
        cookie_accept_btn.click()

        # search
        select_btn = self.driver.find_element_by_css_selector('button[data-id=ooclCargoSelector]')
        select_btn.click()

        search_type_select = Select(self.driver.find_element_by_css_selector('select#ooclCargoSelector'))
        search_type_select.select_by_index(1)

        search_bar = self.driver.find_element_by_css_selector('input#SEARCH_NUMBER')
        search_bar.send_keys(mbl_no)

        search_btn = self.driver.find_element_by_css_selector('a#container_btn')
        search_btn.click()

    def _get_result_search_url(self):
        WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'span#nc_1_n1z'))
        )
        return self.driver.current_url

    def _handle_with_slide(self):
        # slide the verification
        WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'span#nc_1_n1z'))
        )
        tracks = self.get_track(260)
        self.move_to_gap(tracks=tracks)

    def search_mbl(self, mbl_no):
        self._click_cookies_and_search(mbl_no=mbl_no)

        # jump to popup window to get url
        windows = self.driver.window_handles
        self.driver.switch_to.window(windows[1])  # windows[1] is new page
        search_page_url = self._get_result_search_url()
        if self._is_blocked(response=Selector(text=self.driver.page_source)):
            raise RuntimeError()

        # jump back to origin window
        self.driver.switch_to.window(windows[0])
        self.driver.get(search_page_url)

        self._handle_with_slide()

        time.sleep(7)
        return self.driver.page_source

    @staticmethod
    def _is_blocked(response):
        res = response.xpath('/html/body/title/text()').extract()
        if res and str(res[0]) == 'Error':
            return True
        else:
            return False

    def extract_cookies(self):
        cookies = {}
        for cookie in self.driver.get_cookies():
            cookies[cookie['name']] = cookie['value']

        return cookies

    def move_to_gap(self, tracks: List):

        # find slide span
        need_move_span = self.driver.find_element_by_xpath('//*[@id="nc_1_n1t"]/span')
        # click and hold mouse
        ActionChains(self.driver).click_and_hold(need_move_span).perform()
        for x in tracks:  # simulate human's motivation
            print(x)
            ActionChains(self.driver).move_by_offset(xoffset=x, yoffset=random.randint(1, 3)).perform()
        time.sleep(1)
        ActionChains(self.driver).release().perform()

    @staticmethod
    def get_track(distance):
        """
        follow Newton's laws of motion
        ①v=v0+at
        ②s=v0t+(1/2)at²
        ③v²-v0²=2as

        """
        # initial speed
        v = 5
        # record the distance by 0.2 s
        t = 0.2
        # list of every distance of 0.2 s
        tracks = []
        # current distance
        current = 0
        # start to slow until 4/5 of total distance
        mid = distance * 3 / 5

        while current < distance:
            if current < mid:
                a = 30  # slower
            else:
                a = -10  # slower

            # initial speed
            v0 = v
            # move distance in 0.2 s
            s = v0 * t + 0.5 * a * (t ** 2)
            current += s
            tracks.append(round(s))

            # next initial speed
            v = v0 + a * t

        return tracks

    def quit(self):
        self.driver.quit()


class SummaryRightTableLocator(BaseTableLocator):
    TD_TITLE_INDEX = 0
    TD_DATA_INDEX = 1

    def __init__(self):
        self._td_map = {}  # title: td

    def parse(self, table: Selector):
        tr_list = table.css('tr')

        for tr in tr_list:
            td_list = tr.css('td')
            if not td_list:
                continue

            title_td = td_list[self.TD_TITLE_INDEX]
            data_td = td_list[self.TD_DATA_INDEX]

            title_not_strip = title_td.css('::text').get()
            title = title_not_strip.strip() if isinstance(title_not_strip, str) else ''

            self._td_map[title] = data_td

    def get_cell(self, top, left) -> Selector:
        assert left is None
        try:
            return self._td_map[top]
        except (KeyError, IndexError) as err:
            raise HeaderMismatchError(repr(err))

    def has_header(self, top=None, left=None) -> bool:
        return (top in self._td_map) and (left is None)


class RoutingTableLocator(BaseTableLocator):
    """
        +-------------------------------------+ <tbody>
        | Title 1  | Title 2  | ... |   <th>  | <tr>
        +----------+----------+-----+---------+
        | Data 1-1 | Data 2-1 |     |   <td>  | <tr>
        +----------+----------+-----+---------+
        | Data 1-2 | Data 2-2 |     |   <td>  | <tr>
        +----------+----------+-----+---------+
        | ...      | ...      |     |   <td>  | <tr>
        +----------+----------+-----+---------+ </tbody>
    """

    TR_TITLE_INDEX = 0
    TR_DATA_START_INDEX = 1

    FIRST_LEFT_HEADER = 0
    LAST_LEFT_HEADER = -1

    def __init__(self):
        self._td_map = {}  # title: [td, ...]

    def parse(self, table: scrapy.Selector):
        title_tr = table.css('tr')[self.TR_TITLE_INDEX]
        data_trs = table.css('tr')[self.TR_DATA_START_INDEX:]

        raw_title_list = title_tr.css('th::text').getall()
        title_list = [title.strip() for title in raw_title_list if isinstance(title, str)]

        for title_index, title in enumerate(title_list):
            data_index = title_index

            self._td_map[title] = []
            for data_tr in data_trs:
                data_td = data_tr.css('td')[data_index]
                self._td_map[title].append(data_td)

    def get_cell(self, top, left) -> scrapy.Selector:
        try:
            return self._td_map[top][left]
        except KeyError as err:
            raise HeaderMismatchError(repr(err))

    def has_header(self, top=None, left=None) -> bool:
        return (top in self._td_map) and (left is None)


class ContainerTableLocator(BaseTableLocator):
    """
    +---------+---------+-----+-------------------------+-----+ <tbody>  -----+
    | Title 1 | Title 2 | ... |      Latest Event       | ... | <tr> <th>     |
    +---------+---------+-----+-------------------------+-----+               |
    |         |         |     | Event | Location | Time |     | <tr> <th>     |
    +---------+---------+-----+-------------------------+-----+               |
    | Data 1  | Data 2  | ... | Data  |   Data   | Data | ... | <tr> <td>     |
    +---------+---------+-----+-------------------------+-----+ <\tbody> -----+
    """
    TR_MAIN_TITLE_INDEX = 0
    TR_SUB_TITLE_INDEX = 1
    TR_DATA_START_INDEX = 2

    def __init__(self):
        self._td_map = {}  # title: [td, ...]
        self._data_len = 0

    def parse(self, table: scrapy.Selector):
        tr_list = table.xpath('./tr') or table.xpath('./tbody/tr')

        main_title_list = tr_list[self.TR_MAIN_TITLE_INDEX].css('th::text').getall()
        sub_title_list = tr_list[self.TR_SUB_TITLE_INDEX].css('th::text').getall()
        data_tr_list = tr_list[self.TR_DATA_START_INDEX:]

        title_list = []
        for main_title_index, main_title in enumerate(main_title_list):
            main_title = main_title.strip() if isinstance(main_title, str) else ''

            if main_title == 'Latest Event':
                sub_title_list = [sub.strip() for sub in sub_title_list if isinstance(sub, str)]
                title_list.extend(sub_title_list)
            else:
                title_list.append(main_title)

        for title_index, title in enumerate(title_list):
            data_index = title_index

            self._td_map[title] = []
            for data_tr in data_tr_list:
                data_td = data_tr.css('td')[data_index]
                self._td_map[title].append(data_td)

        first_title = title_list[0]
        self._data_len = len(self._td_map[first_title])

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


class VesselVoyageTdExtractor(BaseTableCellExtractor):

    def extract(self, cell: Selector):
        text_list = cell.css('::text').getall()

        if len(text_list) != 2:
            CarrierResponseFormatError(reason=f'Unknown Vessel Voyage td format: `{text_list}`')

        vessel = self._parse_vessel(text_list[0])

        return {
            'vessel': vessel,
            'voyage': text_list[1].strip(),
        }

    @staticmethod
    def _parse_vessel(text):
        """
        Sample 1:
            text = (
                '\n'
                '\t\t\t\t\t\t\t\t\t\t\t\t\t\t  ECC2\n'
                '\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t  EVER LEADER\xa0\n'
                '\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t  '
            )
            result = 'EVER LEADER'

        Sample 2:
            text = (
                '\n'
                '\t\t\t\t\t\t\t\t\t\t\t\t\t\t  SC2\n'
                '\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t  XIN YING KOU\xa0\n'
                '\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t  '
            )
            result = 'XIN YING KOU'
        """
        lines = text.strip().split('\n')

        vessel = lines[1].strip()
        return vessel


class PolPodTdExtractor(BaseTableCellExtractor):

    def extract(self, cell: Selector):
        text_list = cell.css('::text').getall()

        if len(text_list) < 4:
            raise CarrierResponseFormatError(reason=f'Unknown Pol or Pod td format: `{text_list}`')

        return {
            'port': text_list[0].strip(),
            'time_str': text_list[2].strip(),
            'status': text_list[3].strip(),
        }


class DelivTdExtractor(BaseTableCellExtractor):

    def extract(self, cell: Selector):
        text_list = cell.css('::text').getall()

        if len(text_list) < 3:
            raise CarrierResponseFormatError(reason=f'Unknown Deliv td format: `{text_list}`')

        return {
            'port': text_list[0].strip(),
            'time_str': text_list[1].strip(),
            'status': text_list[2].strip(),
        }


# -------------------------------------------------------------------------------


def get_multipart_body(form_data, boundary):
    body = ''
    for index, key in enumerate(form_data):
        body += (
            f'--{boundary}\r\n'
            f'Content-Disposition: form-data; name="{key}"\r\n'
            f'\r\n'
            f'{form_data[key]}\r\n'
        )
    body += f'--{boundary}--'
    return body


class ContainerStatusRule(BaseRoutingRule):
    name = 'CONTAINER_STATUS'

    def __init__(self, driver):
        self._driver = driver

    @classmethod
    def build_request_option(cls, container_no: str, click_element_css: str) -> RequestOption:
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url='https://www.google.com',
            meta={
                'container_no': container_no,
                'click_element_css': click_element_css,
            },
        )

    @staticmethod
    def transform_cookies_to_str(cookies: Dict):
        cookies_str = ''
        for key, value in cookies.items():
            cookies_str += f'{key}={value}; '

        return cookies_str[:-2]

    def get_save_name(self, response) -> str:
        container_no = response.meta['container_no']
        return f'{self.name}_{container_no}.html'

    def handle(self, response):
        container_no = response.meta['container_no']
        click_element_css = response.meta['click_element_css']

        self._driver.find_container_btn_and_click(container_btn_css=click_element_css)
        time.sleep(10)
        response = Selector(text=self._driver.get_page_text())

        locator = _PageLocator()
        selectors_map = locator.locate_selectors(response=response)
        detention_info = self._extract_detention_info(selectors_map)

        yield ContainerItem(
            container_key=container_no,
            container_no=container_no,
            last_free_day=detention_info['last_free_day'] or None,
            det_free_time_exp_date=detention_info['det_free_time_exp_date'] or None,
        )

        container_status_list = self._extract_container_status_list(selectors_map)
        for container_status in container_status_list:
            event = container_status['event']
            facility = container_status['facility']

            if facility:
                description = f'{event} ({facility})'
            else:
                description = event

            yield ContainerStatusItem(
                container_key=container_no,
                description=description,
                location=LocationItem(name=container_status['location']),
                transport=container_status['transport'],
                local_date_time=container_status['local_date_time'],
            )

    @staticmethod
    def _extract_detention_info(selectors_map: Dict[str, scrapy.Selector]):
        table = selectors_map['detail:detention_right_table']

        table_locator = DestinationTableLocator()
        table_locator.parse(table=table)
        table_extractor = TableExtractor(table_locator=table_locator)
        td_extractor = DetentionDateTdExtractor()

        if table_locator.has_header(left='Demurrage Last Free Date:'):
            lfd_info = table_extractor.extract_cell(top=None, left='Demurrage Last Free Date:', extractor=td_extractor)
            _, lfd = _get_est_and_actual(status=lfd_info['status'], time_str=lfd_info['time_str'])
        else:
            lfd = ''

        if table_locator.has_header(left='Detention Last Free Date:'):
            det_lfd_info = table_extractor.extract_cell(top=None, left='Detention Last Free Date:', extractor=td_extractor)
            _, det_lfd = _get_est_and_actual(status=det_lfd_info['status'], time_str=det_lfd_info['time_str'])
        else:
            det_lfd = ''

        return {
            'last_free_day': lfd,
            'det_free_time_exp_date': det_lfd,
        }

    @staticmethod
    def _extract_container_status_list(selectors_map: Dict[str, scrapy.Selector]):
        table = selectors_map['detail:container_status_table']

        table_locator = ContainerStatusTableLocator()
        table_locator.parse(table=table)
        table_extractor = TableExtractor(table_locator=table_locator)
        first_text_extractor = FirstTextTdExtractor()
        span_extractor = FirstTextTdExtractor(css_query='span::text')

        container_status_list = []
        for left in table_locator.iter_left_headers():
            container_status_list.append({
                'event': table_extractor.extract_cell(top='Event', left=left, extractor=first_text_extractor),
                'facility': table_extractor.extract_cell(top='Facility', left=left, extractor=first_text_extractor),
                'location': table_extractor.extract_cell(top='Location', left=left, extractor=span_extractor),
                'transport': table_extractor.extract_cell(
                    top='Mode', left=left, extractor=first_text_extractor) or None,
                'local_date_time': table_extractor.extract_cell(top='Time', left=left, extractor=span_extractor),
            })
        return container_status_list


class ContainerStatusTableLocator(BaseTableLocator):
    """
        +--------------------------------------+ <tbody>
        | Title 1  | Title 2  | ... | Title N  | <tr> <th>
        +----------+----------+-----+----------+
        | Data 1,1 | Data 2,1 | ... | Data N,1 | <tr> <td>
        +----------+----------+-----+----------+
        | Data 1,2 | Data 2,2 | ... | Data N,2 | <tr> <td>
        +----------+----------+-----+----------+
        | ...      | ...      | ... | ...      | <tr> <td>
        +----------+----------+-----+----------+
        | Data 1,M | Data 2,M | ... | Data N,M | <tr> <td>
        +----------+----------+-----+----------+ </tbody>
    """
    DATA_START_TR_INDEX = 1

    def __init__(self):
        self._td_map = {}  # title: [td, ...]
        self._data_len = 0

    def parse(self, table: scrapy.Selector):
        title_list = table.css('th::text').getall()
        data_tr_list = table.css('tr')[self.DATA_START_TR_INDEX:]

        for title_index, title in enumerate(title_list):
            data_index = title_index

            title = title.strip()
            self._td_map[title] = []
            for data_tr in data_tr_list:
                data_td = data_tr.css('td')[data_index]
                self._td_map[title].append(data_td)

        first_title = title_list[0]
        self._data_len = len(self._td_map[first_title])

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


class DestinationTableLocator(BaseTableLocator):
    """
        +--------------------------------+ <tbody>
        | Title 1 | Data 1,1  | Data 1,2 | <tr> <td>
        +---------+-----------+----------+
        | Title 2 | Data 2,1  | Data 2,2 | <tr> <td>
        +---------+-----------+----------+
        | Title 3 | Data 3,1  | Data 3,2 | <tr> <td>
        +---------+-----------+----------+
        | ...     |           |          | <tr> <td>
        +---------+-----------+----------+
        | Title N | Data N,1  | Data N,2 | <tr> <td>
        +---------+-----------+----------+ </tbody>
    """
    TITEL_TD_INDEX = 0
    DATA_NEEDED_TD_INDEX = 2

    def __init__(self):
        self._td_map = {}  # title: td

    def parse(self, table: scrapy.Selector):
        tr_list = table.css('tr')

        for tr in tr_list:
            td_list = tr.css('td')

            title_td = td_list[self.TITEL_TD_INDEX]
            title = title_td.css('::text').get()
            title = title.strip() if isinstance(title, str) else ''
            self._td_map[title] = td_list[self.DATA_NEEDED_TD_INDEX]

    def get_cell(self, top, left) -> scrapy.Selector:
        assert top is None
        try:
            return self._td_map[left]
        except KeyError as err:
            raise HeaderMismatchError(repr(err))

    def has_header(self, top=None, left=None) -> bool:
        return (left in self._td_map) and (top is None)


class DetentionDateTdExtractor(BaseTableCellExtractor):

    def extract(self, cell: Selector):
        text_list = cell.css('::text').getall()
        text_list_len = len(text_list)

        if text_list_len != 2 or text_list_len != 1:
            CarrierResponseFormatError(reason=f'Unknown last free day td format: `{text_list}`')

        return {
            'time_str': text_list[0].strip(),
            'status': text_list[1].strip() if text_list_len == 2 else '',
        }


# -------------------------------------------------------------------------------


class _PageLocator:

    def locate_selectors(self, response: scrapy.Selector):
        tables = response.css('table.groupTable')

        # summary
        summary_rule = CssQueryTextStartswithMatchRule(css_query='td.groupTitle::text', startswith='Summary')
        summary_table = find_selector_from(selectors=tables, rule=summary_rule)
        if not summary_table:
            raise CarrierResponseFormatError(reason='Can not find summary table !!!')
        summary_selectors_map = self._locate_selectors_from_summary(summary_table=summary_table)

        # detail
        detail_rule = CssQueryTextStartswithMatchRule(
            css_query='td.groupTitle::text', startswith='Detail of OOCL Container')
        detail_table = find_selector_from(selectors=tables, rule=detail_rule)
        if not detail_table:
            raise CarrierResponseFormatError(reason='Can not find detail table !!!')
        detail_selectors_map = self._locate_selectors_from_detail(detail_table=detail_table)

        return {
            **summary_selectors_map,
            **detail_selectors_map,
        }

    @staticmethod
    def _locate_selectors_from_summary(summary_table: scrapy.Selector):
        # top table
        top_table = summary_table.xpath('./tr/td/table') or summary_table.xpath('./tbody/tr/td/table')
        if not top_table:
            raise CarrierResponseFormatError(reason='Can not find top_table !!!')

        top_inner_tables = top_table.css('tr table')
        if len(top_inner_tables) != 2:
            raise CarrierResponseFormatError(reason=f'Amount of top_inner_tables not right: `{len(top_inner_tables)}`')

        # bottom table
        bottom_table = summary_table.css('div#summaryDiv > table')
        if not bottom_table:
            raise CarrierResponseFormatError(reason='Can not find container_outer_table !!!')

        bottom_inner_tables = bottom_table.css('tr table')
        if not bottom_inner_tables:
            raise CarrierResponseFormatError(reason='Can not find container_inner_table !!!')

        return {
            'summary:main_left_table': top_inner_tables[0],
            'summary:main_right_table': top_inner_tables[1],
            'summary:container_table': bottom_inner_tables[0],
        }

    def _locate_selectors_from_detail(self, detail_table: scrapy.Selector):
        # routing tab
        routing_tab = detail_table.css('div#Tab1')
        if not routing_tab:
            raise CarrierResponseFormatError(reason='Can not find routing_tab !!!')

        routing_table = routing_tab.css('table#eventListTable')
        if not routing_table:
            raise CarrierResponseFormatError(reason='Can not find routing_table !!!')

        # equipment tab
        equipment_tab = detail_table.css('div#Tab2')
        if not equipment_tab:
            raise CarrierResponseFormatError(reason='Can not find equipment_tab !!!')

        equipment_table = equipment_tab.css('table#eventListTable')
        if not equipment_table:
            raise CarrierResponseFormatError(reason='Can not find equipment_table !!!')

        # detention tab
        detention_tab = detail_table.css('div#Tab3')
        if not detention_tab:
            raise CarrierResponseFormatError(reason='Can not find detention_tab !!!')

        detention_tables = self._locate_detail_detention_tables(detention_tab=detention_tab)

        return {
            'detail:routing_table': routing_table,
            'detail:container_status_table': equipment_table,
            'detail:detention_right_table': detention_tables[1],
        }

    @staticmethod
    def _locate_detail_detention_tables(detention_tab: scrapy.Selector):
        inner_parts = detention_tab.xpath('./table/tr/td/table') or detention_tab.xpath('./table/tbody/tr/td/table')
        if len(inner_parts) != 2:
            raise CarrierResponseFormatError(reason=f'Amount of detention_inner_parts not right: `{len(inner_parts)}`')

        title_part, content_part = inner_parts

        detention_tables = (
            content_part.xpath('./tr/td/table/tr/td/table') or
            content_part.xpath('./tbody/tr/td/table/tbody/tr/td/table')
        )
        if len(detention_tables) != 2:
            raise CarrierResponseFormatError(
                reason=f'Amount of detention tables does not right: {len(detention_tables)}')

        return detention_tables


def _get_est_and_actual(status, time_str):
    if status == '(Actual)':
        estimate, actual = None, time_str
    elif status == '(Estimated)':
        estimate, actual = time_str, ''
    elif status == '':
        estimate, actual = None, ''
    else:
        raise CarrierResponseFormatError(reason=f'Unknown status format: `{status}`')

    return estimate, actual
