import time
import dataclasses
import random
import string
from typing import List, Dict
from datetime import datetime, timedelta
from urllib.parse import urlencode


import scrapy
from scrapy import Selector
# from selenium import webdriver
from seleniumwire import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from anticaptchaofficial.recaptchav2proxyless import *
from selenium.common.exceptions import NoSuchElementException

from crawler.core_carrier.exceptions import LoadWebsiteTimeOutError
from crawler.core_terminal.base_spiders import BaseMultiTerminalSpider
from crawler.core_terminal.items import DebugItem, TerminalItem, InvalidContainerNoItem
from crawler.core_terminal.request_helpers import RequestOption
from crawler.core_terminal.rules import RuleManager, BaseRoutingRule
from crawler.extractors.table_cell_extractors import BaseTableCellExtractor
from crawler.extractors.table_extractors import BaseTableLocator, HeaderMismatchError, TableExtractor


@dataclasses.dataclass
class CompanyInfo:
    lower_short: str
    upper_short: str
    email: str
    password: str

@dataclasses.dataclass
class ProxyOption:
    group: str
    session: str


@dataclasses.dataclass
class SaveItem:
    file_name: str
    text: str


class CookieHelper:
    @staticmethod
    def get_cookies(response):
        cookies = {}
        for cookie_byte in response.headers.getlist('Set-Cookie'):
            kv = cookie_byte.decode('utf-8').split(';')[0].split('=')
            cookies[kv[0]] = kv[1]

        return cookies

    @staticmethod
    def get_cookie_str(cookies: Dict):
        cookies_str = ''
        for item in cookies:
            cookies_str += f"{item['name']}={item['value']}; "

        return cookies_str


class TrapacShareSpider(BaseMultiTerminalSpider):
    name = ''
    company_info = CompanyInfo(
        lower_short='',
        upper_short='',
        email='',
        password='',
    )

    def __init__(self, *args, **kwargs):
        super(TrapacShareSpider, self).__init__(*args, **kwargs)

        rules = [
            MainRoutingRule(),
            ContentRoutingRule()
        ]

        self._rule_manager = RuleManager(rules=rules)
        self._save = True if 'save' in kwargs else False

    def start(self):
        unique_container_nos = list(self.cno_tid_map.keys())
        option = MainRoutingRule.build_request_option(container_no_list=unique_container_nos, company_info=self.company_info)
        yield self._build_request_by(option=option)

    def parse(self, response):
        yield DebugItem(info={'meta': dict(response.meta)})

        routing_rule = self._rule_manager.get_rule_by_response(response=response)

        for result in routing_rule.handle(response=response):
            if isinstance(result, TerminalItem) or isinstance(result, InvalidContainerNoItem):
                c_no = result['container_no']
                t_ids = self.cno_tid_map[c_no]
                for t_id in t_ids:
                    result['task_id'] = t_id
                    yield result
            elif isinstance(result, RequestOption):
                yield self._build_request_by(option=result)
            elif isinstance(result, SaveItem) and self._save:
                self._saver.save(to=result.file_name, text=result.text)
            elif isinstance(result, SaveItem) and not self._save:
                pass

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

        elif option.method == RequestOption.METHOD_POST_BODY:
            return scrapy.Request(
                method='POST',
                url=option.url,
                headers=option.headers,
                body=option.body,
                meta=meta,
                dont_filter=True,
                callback=self.parse,
            )

        else:
            raise ValueError(f'Invalid option.method [{option.method}]')


class MainRoutingRule(BaseRoutingRule):
    name = 'MAIN'

    @classmethod
    def build_request_option(cls, container_no_list: List, company_info: CompanyInfo) -> RequestOption:
        url = 'https://www.google.com'
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=url,
            meta={
                'container_no_list': container_no_list,
                'company_info': company_info,
            },
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.html'

    def handle(self, response):
        company_info = response.meta['company_info']
        container_no_list = response.meta['container_no_list']

        is_g_captcha, res, cookies = self._build_container_response(company_info=company_info, container_no_list=container_no_list)
        if is_g_captcha:
            if res:
                print('print(is_g_captcha, res, cookies)', is_g_captcha, res, cookies)
                yield ContentRoutingRule.build_request_option(container_no_list, company_info=company_info, g_token=res, cookies=cookies)
        else:
            container_response = scrapy.Selector(text=res)
            yield SaveItem(file_name='container.html', text=container_response.get())

            for container_info in self._extract_container_result_table(response=container_response, numbers=len(container_no_list)):
                yield TerminalItem(  # html field
                    container_no=container_info['container_no'],  # number
                    last_free_day=container_info['last_free_day'],  # demurrage-lfd
                    customs_release=container_info.get('custom_release'),  # holds-customs
                    demurrage=container_info['demurrage'],  # demurrage-amt
                    container_spec=container_info['container_spec'],  # dimensions
                    holds=container_info['holds'],  # demurrage-hold
                    cy_location=container_info['cy_location'],  # yard status
                    vessel=container_info['vessel'],  # vsl / voy
                    voyage=container_info['voyage'],  # vsl / voy
                )

    @staticmethod
    def _build_container_response(company_info: CompanyInfo, container_no_list: List):
        content_getter = ContentGetter(company_info=company_info)
        is_g_captcha, res, cookies = content_getter.get_content(search_no=','.join(container_no_list))
        content_getter.quit()

        return is_g_captcha, res, cookies

    @staticmethod
    def _is_search_no_invalid(response: scrapy.Selector) -> bool:
        return bool(response.css('tr.error-row'))


class ContentRoutingRule(BaseRoutingRule):
    name = 'CONTENT'

    @classmethod
    def build_request_option(cls, container_no_list: Dict, company_info: CompanyInfo, g_token: str, cookies: Dict) -> RequestOption:
        form_data = {
            'action': 'trapac_transaction',
            'recaptcha-token': g_token,
            'terminal': company_info.upper_short,
            'transaction': 'availability',
            'containers': ','.join(container_no_list),
            'container': '',
            'booking': '',
            'email': '',
            'equipment_type': 'CT',
            'history_type': 'N',
            'services': '',
            'from_date': str(datetime.now().date()),
            'to_date': str((datetime.now() + timedelta(days=30)).date())
        }

        headers = {
            'authority': f'{company_info.lower_short}.trapac.com',
            'sec-ch-ua': '"Google Chrome";v="89", "Chromium";v="89", ";Not A Brand";v="99"',
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'x-requested-with': 'XMLHttpRequest',
            'sec-ch-ua-mobile': '?0',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_1_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.128 Safari/537.36',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'origin': f'https://{company_info.lower_short}.trapac.com',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'cors',
            'sec-fetch-dest': 'empty',
            'referer': f'https://{company_info.lower_short}.trapac.com/quick-check/?terminal=',
            'accept-language': 'en-US,en;q=0.9',
            'cookie': CookieHelper.get_cookie_str(cookies),
        }

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_POST_BODY,
            url=f'https://{company_info.lower_short}.trapac.com/wp-admin/admin-ajax.php',
            headers=headers,
            body=urlencode(query=form_data),
            meta={
                'numbers': len(container_no_list),
            },
        )

    def handle(self, response):
        numbers = response.meta['numbers']

        print('paul response.body', numbers, response.body)
        self._extract_container_result_table(response, numbers)
        yield

    @staticmethod
    def _extract_container_result_table(response: scrapy.Selector, numbers: int):
        table = response.css('div[class="transaction-result availability"] table')

        table_locator = ContainerTableLocator()
        table_locator.parse(table=table, numbers=numbers)
        table_extractor = TableExtractor(table_locator=table_locator)

        vessel, voyage = table_extractor.extract_cell(top='Vsl / Voy', left=0, extractor=VesselVoyageTdExtractor())

        for i in range(numbers):
            yield {
                'container_no': table_extractor.extract_cell(top='Number', left=i),
                'carrier': table_extractor.extract_cell(top='Holds_Line', left=i),
                'custom_release': table_extractor.extract_cell(top='Holds_Customs', left=i),
                'cy_location': table_extractor.extract_cell(top='Yard Status', left=i),
                'last_free_day': table_extractor.extract_cell(top='Demurrage_LFD', left=i),
                'holds': table_extractor.extract_cell(top='Demurrage_Hold', left=i),
                'demurrage': table_extractor.extract_cell(top='Demurrage_Amt', left=i),
                'container_spec': table_extractor.extract_cell(top='Dimensions', left=i),
                'vessel': vessel,
                'voyage': voyage,
            }

# ------------------------------------------------------------------------


class HeadlessBrowser:

    PROXY_URL = 'proxy.apify.com:8000'
    PROXY_PASSWORD = 'XZTBLpciyyTCFb3378xWJbuYY'

    def __init__(self):

        options = webdriver.ChromeOptions()
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-notifications')
        options.add_argument('--headless')
        options.add_argument("--enable-javascript")
        options.add_argument("window-size=1920,1080")
        options.add_argument(
            f'user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 11_1_0) AppleWebKit/537.36 (KHTML, like Gecko) '
            f'Chrome/88.0.4324.96 Safari/537.36'
        )
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)

        # PROXY_GROUP_SHADER = 'SHADER'
        # PROXY_GROUP_RESIDENTIAL = 'RESIDENTIAL'
        # proxy_option = ProxyOption(group=PROXY_GROUP_SHADER, session=f'trapac{self._generate_random_string()}')
        # seleniumwire_options = {
        #     'connection_timeout': None,
        #     'proxy': {
        #         'http': f'http://{self.get_proxy_username(proxy_option)}:{self.PROXY_PASSWORD}@{self.PROXY_URL}',
        #         'https': f'https://{self.get_proxy_username(proxy_option)}:{self.PROXY_PASSWORD}@{self.PROXY_URL}',
        #         'no_proxy': 'localhost,127.0.0.1'
        #     }
        # }
        # self._browser = webdriver.Chrome(chrome_options=options, seleniumwire_options=seleniumwire_options)
        self._browser = webdriver.Chrome(chrome_options=options)

    def get(self, url):
        self._browser.get(url=url)
        time.sleep(15)

    def accept_cookie(self):
        cookie_btn = self._browser.find_element_by_xpath('//*[@id="cn-accept-cookie"]')
        cookie_btn.click()
        time.sleep(3)

    def wait_for_appear(self, css: str, wait_sec: int):
        locator = (By.CSS_SELECTOR, css)
        try:
            WebDriverWait(self._browser, wait_sec).until(EC.presence_of_element_located(locator))
        except TimeoutException:
            current_url = self._browser.current_url
            self._browser.quit()
            raise LoadWebsiteTimeOutError(url=current_url)

    def key_in_search_bar(self, search_no: str):
        text_area = self._browser.find_element_by_xpath('//*[@id="edit-containers"]')
        text_area.send_keys(search_no)
        time.sleep(3)

    def press_search_button(self):
        search_btn = self._browser.find_element_by_xpath('//*[@id="transaction-form"]/div[3]/button')
        search_btn.click()
        time.sleep(10)

    def find_element_by_css_selector(self, css: str):
        return self._browser.find_element_by_css_selector(css_selector=css)

    def execute_script(self, script: str):
        self._browser.execute_script(script=script)

    def quit(self):
        self._browser.quit()

    def get_cookies(self):
        return self._browser.get_cookies()

    def save_screenshot(self):
        self._browser.save_screenshot("screenshot.png")

    def get_google_recaptcha(self):
        try:
            element = self._browser.find_element_by_xpath('//*[@id="recaptcha-backup"]')
            return element
        except NoSuchElementException:
            return None

    def solve_google_recaptcha(self, location_name: str):
        solver = recaptchaV2Proxyless()
        solver.set_verbose(1)
        solver.set_key("f7dd6de6e36917b41d05505d249876c3")
        solver.set_website_url(f"https://{location_name}.trapac.com/")
        solver.set_website_key("6LfCy7gUAAAAAHSPtJRrJIVQKeKQt_hrYbGSIpuF")

        g_response = solver.solve_and_return_solution()

        if g_response != 0:
            print("g-response: " + g_response)
            return g_response
        else:
            print("task finished with error " + solver.error_code)
            return None

    @property
    def page_source(self):
        return self._browser.page_source

    def get_proxy_username(self, option: ProxyOption) -> str:
        return f'groups-{option.group},session-{option.session}'

    @staticmethod
    def _generate_random_string():
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=20))


class ContentGetter:
    def __init__(self, company_info: CompanyInfo):
        self._company = company_info
        self._headless_browser = HeadlessBrowser()

    def find_ua(self):
        self._headless_browser.get('https://www.whatsmyua.info')
        ua_selector = self._headless_browser.find_element_by_css_selector(css='textarea#custom-ua-string')
        print('find_ua:', ua_selector.text)

    def find_ip(self):
        self._headless_browser.get('https://www.whatismyip.com.tw/')
        time.sleep(3)

        ip_selector = self._headless_browser.find_element_by_css_selector('b span')
        print('find_id', ip_selector.text)

    def get_result_response_text(self):
        result_table_css = 'div#transaction-detail-result table'

        self._headless_browser.wait_for_appear(css=result_table_css, wait_sec=15)
        return self._headless_browser.page_source

    def get_content(self, search_no):
        self._headless_browser.get(
            url=f'https://{self._company.lower_short}.trapac.com/quick-check/?terminal={self._company.upper_short}&transaction=availability'
        )
        self._headless_browser.accept_cookie()
        self._headless_browser.key_in_search_bar(search_no=search_no)
        self._headless_browser.press_search_button()
        cookies = self._headless_browser.get_cookies()
        if self._headless_browser.get_google_recaptcha():
            g_response = self._headless_browser.solve_google_recaptcha(self._company.lower_short)
            return True, g_response, cookies

        time.sleep(20)
        self._headless_browser.save_screenshot()

        return False, self.get_result_response_text(), cookies

    def quit(self):
        self._headless_browser.quit()


class VesselVoyageTdExtractor(BaseTableCellExtractor):
    def extract(self, cell: Selector):
        vessel_voyage = cell.css('::text').get()
        vessel, voyage = vessel_voyage.split('/')
        return vessel, voyage


class ContainerTableLocator(BaseTableLocator):
    TR_MAIN_TITLE_CLASS = 'th-main'
    TR_SECOND_TITLE_CLASS = 'th-second'

    def __init__(self):
        self._td_map = []

    def parse(self, table: Selector, numbers: int = 1):
        main_title_tr = table.css(f'tr.{self.TR_MAIN_TITLE_CLASS}')
        second_title_tr = table.css(f'tr.{self.TR_SECOND_TITLE_CLASS}')
        data_tr = table.css('tbody tr')

        main_title_ths = main_title_tr.css('th')
        second_title_ths = second_title_tr.css('th')
        title_list = self.__combine_title_list(main_title_ths=main_title_ths, second_title_ths=second_title_ths)

        for i in range(len(data_tr)):
            if i >= numbers:
                continue
            data_tds = data_tr[i].css('td')
            row = {}
            for title_index, title in enumerate(title_list):
                row[title] = data_tds[title_index]
            self._td_map.append(row)

    def has_header(self, top=None, left=None) -> bool:
        return (top in self._td_map) and (left is None)

    def get_cell(self, top, left=0) -> scrapy.Selector:
        try:
            return self._td_map[left][top]
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
