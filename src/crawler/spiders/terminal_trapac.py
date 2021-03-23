import time
from dataclasses import dataclass
from enum import Enum
from typing import List

import scrapy
from scrapy import Selector
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from crawler.core_carrier.exceptions import LoadWebsiteTimeOutError
from crawler.core_terminal.base_spiders import BaseTerminalSpider
from crawler.core_terminal.exceptions import TerminalInvalidContainerNoError, TerminalInvalidMblNoError
from crawler.core_terminal.items import DebugItem, BaseTerminalItem, TerminalItem
from crawler.core_terminal.request_helpers import RequestOption
from crawler.core_terminal.rules import RuleManager, BaseRoutingRule
from crawler.extractors.table_cell_extractors import BaseTableCellExtractor
from crawler.extractors.table_extractors import BaseTableLocator, HeaderMismatchError, TableExtractor


class Location(Enum):
    LOS_ANGELES = 'LAX'
    OAKLAND = 'OAK'
    JACKSONWILLE = 'JAX'


@dataclass
class SaveItem:
    file_name: str
    text: str


class ShareSpider(BaseTerminalSpider):
    name = None
    location = None

    def __init__(self, *args, **kwargs):
        super(ShareSpider, self).__init__(*args, **kwargs)

        rules = [
            ContentRoutingRule()
        ]

        self._rule_manager = RuleManager(rules=rules)
        self._save = True if 'save' in kwargs else False

    def start(self):
        option = ContentRoutingRule.build_request_option(
            container_no=self.container_no, mbl_no=self.mbl_no, location=self.location)
        yield self._build_request_by(option=option)

    def parse(self, response):
        yield DebugItem(info={'meta': dict(response.meta)})

        routing_rule = self._rule_manager.get_rule_by_response(response=response)

        for result in routing_rule.handle(response=response):
            if isinstance(result, BaseTerminalItem):
                yield result
            elif isinstance(result, RequestOption):
                yield self._build_request_by(option=result)
            elif isinstance(result, SaveItem) and self._save:
                self._saver.save(to=result.file_name, text=result.text)
            elif isinstance(result, SaveItem) and not self._save:
                pass
            else:
                raise RuntimeError()

    def _build_request_by(self, option: RequestOption):
        meta = {
            RuleManager.META_TERMINAL_CORE_RULE_NAME: option.rule_name,
            **option.meta,
        }

        if option.method == RequestOption.METHOD_GET:
            return scrapy.Request(
                url=option.url,
                meta=meta,
            )
        else:
            raise ValueError(f'Invalid option.method [{option.method}]')


class TerminalTraPacLASpider(ShareSpider):
    name = 'terminal_trapac_la'
    location = Location.LOS_ANGELES.value


# ---------------------------------------------------------------------------------------


class ContentRoutingRule(BaseRoutingRule):
    name = 'CONTENT'

    @classmethod
    def build_request_option(cls, location, container_no, mbl_no=None) -> RequestOption:
        url = 'https://www.google.com'
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=url,
            meta={
                'mbl_no': mbl_no,
                'container_no': container_no,
                'location': location,
            },
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.html'

    def handle(self, response):
        location = response.meta['location']
        mbl_no = response.meta['mbl_no']
        container_no = response.meta['container_no']

        container_response = self._build_container_response(location=location, container_no=container_no)
        yield SaveItem(file_name='container.html', text=container_response.get())

        if self._is_search_no_invalid(response=container_response):
            raise TerminalInvalidContainerNoError()
        container_info = self._extract_container_result_table(response=container_response)

        mbl_info = {}
        if mbl_no:
            mbl_no_response = self._build_mbl_response(location=location, mbl_no=mbl_no)
            yield SaveItem(file_name='mbl_no.html', text=mbl_no_response.get())

            if self._is_search_no_invalid(response=mbl_no_response):
                raise TerminalInvalidMblNoError()
            mbl_info = self._extract_mbl_no_result_table(response=mbl_no_response)

        yield TerminalItem(  # html field
            container_no=container_info['container_no'],  # number
            last_free_day=container_info['last_free_day'],  # demurrage-lfd
            customs_release=mbl_info.get('custom_release'),  # holds-customs
            # demurrage=container_info['demurrage'],  # demurrage-amt
            # container_spec=container_info['container_spec'],  # dimensions
            # holds=container_info['holds'],  # demurrage-hold
            # cy_location=container_info['cy_location'],  # yard status
            # vessel=container_info['vessel'],  # vsl / voy
            # voyage=container_info['voyage'],  # vsl / voy
            # carrier=mbl_info.get('carrier'),  # mbl holds-line
            # mbl_no=mbl_info.get('mbl_no'),  # mbl number
        )

    @staticmethod
    def _build_container_response(location, container_no):
        content_getter = ContentGetter(location=location)
        container_response_text = content_getter.get_content(search_no=container_no)
        content_getter.quit()

        return scrapy.Selector(text=container_response_text)

    @staticmethod
    def _build_mbl_response(location, mbl_no):
        content_getter = ContentGetter(location=location)
        mbl_response_text = content_getter.get_content(search_no=mbl_no)
        content_getter.quit()

        return scrapy.Selector(text=mbl_response_text)

    @staticmethod
    def _is_search_no_invalid(response: scrapy.Selector) -> bool:
        return bool(response.css('tr.error-row'))

    @staticmethod
    def _extract_container_result_table(response: scrapy.Selector):
        table = response.css('div[class="transaction-result availability"] table')

        table_locator = ContainerTableLocator()
        table_locator.parse(table=table)
        table_extractor = TableExtractor(table_locator=table_locator)

        vessel, voyage = table_extractor.extract_cell(top='Vsl / Voy', left=0, extractor=VesselVoyageTdExtractor())

        return {
            'container_no': table_extractor.extract_cell(top='Number', left=0),
            'carrier': table_extractor.extract_cell(top='Holds_Line', left=0),
            'custom_release': table_extractor.extract_cell(top='Holds_Customs', left=0),
            'cy_location': table_extractor.extract_cell(top='Yard Status', left=0),
            'last_free_day': table_extractor.extract_cell(top='Demurrage_LFD', left=0),
            'holds': table_extractor.extract_cell(top='Demurrage_Hold', left=0),
            'demurrage': table_extractor.extract_cell(top='Demurrage_Amt', left=0),
            'container_spec': table_extractor.extract_cell(top='Dimensions', left=0),
            'vessel': vessel,
            'voyage': voyage,
        }

    @staticmethod
    def _extract_mbl_no_result_table(response: scrapy.Selector):
        table = response.css('div[class="transaction-result availability"] table')

        table_locator = MblTableLocator()
        table_locator.parse(table=table)
        table_extractor = TableExtractor(table_locator=table_locator)

        vessel, voyage = table_extractor.extract_cell(top='Vsl / Voy', left=0, extractor=VesselVoyageTdExtractor())

        return {
            'mbl_no': table_extractor.extract_cell(top='Number', left=0),
            'carrier': table_extractor.extract_cell(top='Holds_Line', left=0),
            'custom_release': table_extractor.extract_cell(top='Holds_Customs', left=0),
            'cy_location': table_extractor.extract_cell(top='Yard Status', left=0),
            'container_spec': table_extractor.extract_cell(top='Dimensions', left=0),
            'vessel': vessel,
            'voyage': voyage,
        }


class VesselVoyageTdExtractor(BaseTableCellExtractor):
    def extract(self, cell: Selector):
        vessel_voyage = cell.css('::text').get()
        vessel, voyage = vessel_voyage.split('/')
        return vessel, voyage


class ContainerTableLocator(BaseTableLocator):
    TR_MAIN_TITLE_CLASS = 'th-main'
    TR_SECOND_TITLE_CLASS = 'th-second'

    def __init__(self):
        self._td_map = {}  # title : td

    def parse(self, table: Selector):
        main_title_tr = table.css(f'tr.{self.TR_MAIN_TITLE_CLASS}')
        second_title_tr = table.css(f'tr.{self.TR_SECOND_TITLE_CLASS}')
        data_tr = table.css('tbody tr')

        main_title_ths = main_title_tr.css('th')
        second_title_ths = second_title_tr.css('th')
        data_tds = data_tr.css('td')

        title_list = self.__combine_title_list(main_title_ths=main_title_ths, second_title_ths=second_title_ths)

        for title_index, title in enumerate(title_list):
            data_index = title_index

            self._td_map[title] = data_tds[data_index]

    def has_header(self, top=None, left=None) -> bool:
        return (top in self._td_map) and (left is None)

    def get_cell(self, top, left=0) -> scrapy.Selector:
        assert left == 0

        try:
            return self._td_map[top]
        except (KeyError, IndexError) as err:
            raise HeaderMismatchError(repr(err))

    @staticmethod
    def __combine_title_list(main_title_ths: List[scrapy.Selector], second_title_ths: List[scrapy.Selector]):
        main_title_list = []
        main_title_accumulated_col_span = []  # [(main_title, accumulated_col_span)]

        accumulated_col_span = 0
        for main_title_th in main_title_ths:
            main_title = ''.join(main_title_th.css('::text').getall())
            col_span = main_title_th.css('::attr(colspan)').get()
            col_span = int(col_span) if col_span else 1

            accumulated_col_span += col_span
            main_title_list.append(main_title)
            main_title_accumulated_col_span.append((main_title, accumulated_col_span))

        title_list = []
        main_title_index = 0
        main_title, accumulated_col_span = main_title_accumulated_col_span[main_title_index]
        for second_title_index, second_title_th in enumerate(second_title_ths):
            second_title = second_title_th.css('::text').get()

            if second_title in ['Size']:
                second_title = None
            elif second_title in ['Type', 'Height']:
                continue

            if second_title_index >= accumulated_col_span:
                main_title_index += 1
                main_title, accumulated_col_span = main_title_accumulated_col_span[main_title_index]

            if second_title:
                title_list.append(f'{main_title}_{second_title}')
            else:
                title_list.append(main_title)

        return title_list


class MblTableLocator(BaseTableLocator):
    TR_MAIN_TITLE_CLASS = 'th-main'
    TR_SECOND_TITLE_CLASS = 'th-second'

    def __init__(self):
        self._td_map = {}  # title : td

    def parse(self, table: Selector):
        main_title_tr = table.css(f'tr.{self.TR_MAIN_TITLE_CLASS}')
        second_title_tr = table.css(f'tr.{self.TR_SECOND_TITLE_CLASS}')
        data_tr = table.css('tbody tr')

        main_title_ths = main_title_tr.css('th')
        second_title_ths = second_title_tr.css('th')
        data_tds = data_tr.css('td')

        title_list = self.__combine_title_list(main_title_ths=main_title_ths, second_title_ths=second_title_ths)

        for title_index, title in enumerate(title_list):
            data_index = title_index

            self._td_map[title] = data_tds[data_index]

    def has_header(self, top=None, left=None) -> bool:
        return (top in self._td_map) and (left is None)

    def get_cell(self, top, left=0) -> scrapy.Selector:
        assert left == 0

        try:
            return self._td_map[top]
        except (KeyError, IndexError) as err:
            raise HeaderMismatchError(repr(err))

    @staticmethod
    def __combine_title_list(main_title_ths: List[scrapy.Selector], second_title_ths: List[scrapy.Selector]):
        main_title_list = []
        main_title_accumulated_col_span = []  # [(main_title, accumulated_col_span)]

        accumulated_col_span = 0
        for main_title_th in main_title_ths:
            main_title = ''.join(main_title_th.css('::text').getall())
            col_span = main_title_th.css('::attr(colspan)').get()
            col_span = int(col_span) if col_span else 1

            accumulated_col_span += col_span
            main_title_list.append(main_title)
            main_title_accumulated_col_span.append((main_title, accumulated_col_span))

        title_list = []
        main_title_index = 0
        main_title, accumulated_col_span = main_title_accumulated_col_span[main_title_index]
        for second_title_index, second_title_th in enumerate(second_title_ths):
            second_title = second_title_th.css('::text').get()

            if second_title in ['Size', 'LFD']:
                second_title = None
            elif second_title in ['Type', 'Height', 'Amt', 'Hold']:
                continue

            if second_title_index >= accumulated_col_span:
                main_title_index += 1
                main_title, accumulated_col_span = main_title_accumulated_col_span[main_title_index]

            if second_title:
                title_list.append(f'{main_title}_{second_title}')
            else:
                title_list.append(main_title)

        return title_list


# ------------------------------------------------------------------------


class HeadlessFirefoxBrowser:

    def __init__(self):
        options = webdriver.FirefoxOptions()
        options.add_argument('--disable-extensions')
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument('--window-size=1920,1080')

        self._browser = webdriver.Firefox(firefox_options=options, service_log_path='/dev/null')

    def get(self, url):
        self._browser.get(url=url)

    def wait_for_appear(self, css: str, wait_sec: int):
        locator = (By.CSS_SELECTOR, css)
        try:
            WebDriverWait(self._browser, wait_sec).until(EC.presence_of_element_located(locator))
        except TimeoutException:
            current_url = self._browser.current_url
            self._browser.quit()
            raise LoadWebsiteTimeOutError(url=current_url)

    def find_element_by_css_selector(self, css: str):
        return self._browser.find_element_by_css_selector(css_selector=css)

    def execute_script(self, script: str):
        self._browser.execute_script(script=script)

    def quit(self):
        self._browser.quit()

    @property
    def page_source(self):
        return self._browser.page_source


class ContentGetter:

    def __init__(self, location):
        self._location = location
        self._headless_browser = HeadlessFirefoxBrowser()

    def find_ua(self):
        self._headless_browser.get('https://www.whatsmyua.info')
        time.sleep(3)

        ua_selector = self._headless_browser.find_element_by_css_selector(css='textarea#custom-ua-string')
        print(ua_selector.text)

    def find_ip(self):
        self._headless_browser.get('https://www.whatismyip.com.tw/')
        time.sleep(3)

        ip_selector = self._headless_browser.find_element_by_css_selector('b span')
        print(ip_selector.text)

    def key_in_search_bar(self, search_no: str):
        js = "var q=document.documentElement.scrollTop=0"
        self._headless_browser.execute_script(js)
        time.sleep(3)

        search_bar_css = 'textarea#edit-containers'
        self._headless_browser.wait_for_appear(css=search_bar_css, wait_sec=4)

        search_bar = self._headless_browser.find_element_by_css_selector(search_bar_css)
        search_bar.send_keys(search_no)

    def press_search_button(self):
        search_button_css = 'button[type="submit"]'
        self._headless_browser.wait_for_appear(css=search_button_css, wait_sec=4)

        search_button = self._headless_browser.find_element_by_css_selector(css=search_button_css)
        search_button.click()

    def get_result_response_text(self):
        result_table_css = 'div#transaction-detail-result table'

        self._headless_browser.wait_for_appear(css=result_table_css, wait_sec=10)
        return self._headless_browser.page_source

    def get_content(self, search_no):
        self._headless_browser.get(
            url=f'https://losangeles.trapac.com/quick-check/?terminal={self._location}&transaction=availability'
        )
        self.key_in_search_bar(search_no=search_no)
        self.press_search_button()
        return self.get_result_response_text()

    def quit(self):
        self._headless_browser.quit()

