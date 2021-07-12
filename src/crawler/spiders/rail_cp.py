import random
import time
from typing import List

import scrapy
from scrapy import Selector

from crawler.core_rail.base_spiders import BaseMultiRailSpider
from crawler.core_rail.exceptions import DriverMaxRetryError, RailInvalidContainerNoError
from crawler.core_rail.items import BaseRailItem, RailItem, DebugItem, InvalidContainerNoItem
from crawler.core_rail.request_helpers import RequestOption
from crawler.core_rail.rules import RuleManager, BaseRoutingRule
from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = 'https://www8.cpr.ca'
MAX_RETRY_COUNT = 3


class Restart:
    pass


class RailCPSpider(BaseMultiRailSpider):
    name = 'rail_cacpr'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        rules = [
            ContainerRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)
        self._retry_count = 0

    def start(self):
        yield self._prepare_restart()

    def _prepare_restart(self):
        if self._retry_count > MAX_RETRY_COUNT:
            raise DriverMaxRetryError()

        self._retry_count += 1
        uni_container_nos = list(self.cno_tid_map.keys())
        option = ContainerRoutingRule.build_request_option(container_nos=uni_container_nos)
        return self._build_request_by(option=option)

    def parse(self, response):
        yield DebugItem(info={'meta': dict(response.meta)})

        routing_rule = self._rule_manager.get_rule_by_response(response=response)

        save_name = routing_rule.get_save_name(response=response)
        self._saver.save(to=save_name, text=response.text)

        for result in routing_rule.handle(response=response):
            if isinstance(result, RailItem) or isinstance(result, InvalidContainerNoItem):
                c_no = result['container_no']
                t_ids = self.cno_tid_map[c_no]
                for t_id in t_ids:
                    result['task_id'] = t_id
                    yield result
            elif isinstance(result, BaseRailItem):
                yield result
            elif isinstance(result, RequestOption):
                yield self._build_request_by(option=result)
            elif isinstance(result, Restart):
                yield self._prepare_restart()
            else:
                raise RuntimeError()

    def _build_request_by(self, option: RequestOption):
        meta = {
            RuleManager.META_RAIL_CORE_RULE_NAME: option.rule_name,
            **option.meta,
        }

        if option.method == RequestOption.METHOD_POST_BODY:
            return scrapy.Request(
                method='POST',
                url=option.url,
                headers=option.headers,
                body=option.body,
                meta=meta,
                dont_filter=True,
            )

        elif option.method == RequestOption.METHOD_GET:
            return scrapy.Request(
                url=option.url,
                meta=meta,
                dont_filter=True,
            )

        else:
            raise KeyError()


class ContainerRoutingRule(BaseRoutingRule):
    name = 'CONTAINER'

    def __init__(self):
        self._retry_count = 0

    @classmethod
    def build_request_option(cls, container_nos) -> RequestOption:
        url = 'https://www.google.com'

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=url,
            meta={'container_nos': container_nos},
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.json'

    def handle(self, response):
        container_nos = response.meta['container_nos']

        content_getter = ContentGetter()
        try:
            response_text = content_getter.search(container_nos=container_nos)
        except StaleElementReferenceException:
            content_getter.quit()
            yield Restart()
            return

        response = scrapy.Selector(text=response_text)

        container_infos = self._extract_container_infos(response=response, container_nos=container_nos, content_getter=content_getter)

        for c_no in container_nos:
            info = container_infos[c_no]

            if info['load_empty'] == '':
                yield InvalidContainerNoItem(container_no=c_no)
                continue

            yield RailItem(
                container_no=c_no,
                last_event=info['last_event'],
                last_event_location=info['last_event_location'],
                last_event_time=info['last_event_time'],
                eta=info['eta'],
                ata=info['ata'],
                last_free_day=info['last_free_day'],
            )

    @staticmethod
    def _extract_container_infos(response: scrapy.Selector, container_nos: List, content_getter):
        container_no_header_table = response.css('table[id$=header-fixed-fixrow]') # header table (container_no)
        container_no_content_table = response.css('div > table[id$=-table-fixed]') # content table (container_no)
        container_info_header_table = response.css('div.sapUiTableCtrlScr > table') # header table (container_info)
        container_info_content_table = response.css('div.sapUiTableCtrlCnt > table[id$=-table]') # content table (container_info)

        cno_map = {cno[:-1]: cno for cno in container_nos}
        n_queries = len(container_nos)

        container_no_table_parser = ContainerNoTableParser(content_getter=content_getter,
                                                           header_table=container_no_header_table,
                                                           content_table=container_no_content_table)
        container_info_table_parser = ContainerInfoTableParser(content_getter=content_getter,
                                                               header_table=container_info_header_table,
                                                               content_table=container_info_content_table)
        table_parser = TableParser(content_getter=content_getter,
                                   container_no_table_parser=container_no_table_parser,
                                   container_info_table_parser=container_info_table_parser,
                                   n_queries=n_queries)

        table_parser.parse()

        container_infos = {}
        for container_info in table_parser.get():
            container_info = dict(container_info[0], **container_info[1])

            container_no = cno_map[container_info['Equipment']] # map to original input container_no
            load_empty = container_info['Load/Empty'] # check this for invalid container_no

            last_reported = container_info['Last Reported Station']
            last_event_location, last_event_time = '', ''

            if last_reported:
                last_reported = last_reported.split()[1:]
                last_event_location = ' '.join(last_reported[:-1])
                last_event_time = last_reported[-1]

            last_event = container_info['Equipment Status'] + ', ' + container_info['Load Status']

            xta = container_info['ETA'].split('\n')
            head, value, eta, ata = '', '', '', ''
            if len(xta) > 1:
                head, value = xta[0], xta[1]

            if head == 'ETA':
                eta = value
            else: # 'Arrived on'
                ata = value

            container_infos[container_no] = {
                'load_empty': load_empty,
                'last_event_location': last_event_location,
                'last_event_time': last_event_time,
                'last_event': last_event,
                'eta': eta,
                'ata': ata,
                'last_free_day': container_info['Last Free Day'],
            }

        return container_infos


class TableParser:
    def __init__(self, content_getter, container_no_table_parser, container_info_table_parser, n_queries):
        self._content_getter = content_getter
        self._container_no_table_parser = container_no_table_parser
        self._container_info_table_parser = container_info_table_parser
        self.n_queries = n_queries
        self._items = []

    def parse(self):
        container_no_items = self._container_no_table_parser.parse()
        container_info_items = self._container_info_table_parser.parse()

        for i in range(self.n_queries - 5):
            self._content_getter.scroll_to_next_row()
            container_no_items.append(self._container_no_table_parser.parse_last_row())
            container_info_items.append(self._container_info_table_parser.parse_last_row())

        self._items = zip(container_no_items, container_info_items)

    def get(self):
        return self._items


class ContainerNoTableParser:
    def __init__(self, content_getter, header_table: Selector, content_table: Selector):
        self._content_getter = content_getter
        self._header_table = header_table
        self._content_table = content_table

    def parse(self):
        items = []
        for tr in self._content_table.css('tbody tr'):
            td = tr.css('td')[1]
            container_no = td.css('a::text').get()
            if container_no:
                items.append({"Equipment": container_no})
        return items

    def parse_last_row(self):
        new_page = Selector(text=self._content_getter.get_page_source())
        table = new_page.css('div > table[id$=-table-fixed]')
        tr = table.css('tr.sapUiTableLastRow')
        td = tr.css('td')[1]
        container_no = td.css('a::text').get()
        if container_no:
            return {"Equipment": container_no}


class ContainerInfoTableParser:
    def __init__(self, content_getter, header_table: Selector, content_table: Selector):
        self._content_getter = content_getter
        self._header_table = header_table
        self._headers = []

        self._content_table = content_table
        self._header_set = {
            'Load/Empty',
            'Last Reported Station',
            'Equipment Status',
            'Load Status',
            'ETA',
            'Last Free Day',
        }

    def parse(self):
        self._headers = self._header_table.css('tbody > tr > td span::text').getall()

        items = []
        for tr in self._content_table.css('tbody > tr'):
            content_list = self.get_content_list(tr=tr)

            info_dict = {}
            for i, content in enumerate(content_list):
                header = self._headers[i]
                if header in self._header_set:
                    info_dict[header] = content if content else ''

            items.append(info_dict)

        return items

    def parse_last_row(self):
        new_page = Selector(text=self._content_getter.get_page_source())
        table = new_page.css('div.sapUiTableCtrlCnt > table[id$=-table]')
        last_row = table.css('tr.sapUiTableLastRow')

        content_list = self.get_content_list(last_row)
        info_dict = {}
        for i, content in enumerate(content_list):
            header = self._headers[i]
            if header in self._header_set:
                info_dict[header] = content if content else ''
        return info_dict

    def get_content_list(self, tr: Selector):
        content_list = []
        for td in tr.css('td')[:-1]:
            content = td.css('div>span::text').get()
            content_list.append(content)

        return content_list


class ContentGetter:
    USER_NAME = 'gftracking'
    PASS_WORD = 'GoFt2021'

    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-notifications')
        options.add_argument('--headless')
        options.add_argument("--enable-javascript")
        options.add_argument('--disable-gpu')
        options.add_argument(
            f'user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 11_1_0) AppleWebKit/537.36 (KHTML, like Gecko) '
            f'Chrome/88.0.4324.96 Safari/537.36'
        )
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument('window-size=1200x600')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)

        self._driver = webdriver.Chrome(options=options)
        # self._driver.get('https://www8.cpr.ca/f5idp/saml/idp/profile/redirectorpost/sso')
        self._driver.get('https://www8.cpr.ca/cx/sap/bc/ui5_ui5/ui2/ushell/shells/abap/Fiorilaunchpad.html?#Shell-home')
        self._is_first = True

    def _login(self):
        # login
        username_input = WebDriverWait(self._driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input#username'))
        )
        password_input = self._driver.find_element_by_id('password')

        time.sleep(random.randint(1, 3))
        username_input.send_keys(self.USER_NAME)
        password_input.send_keys(self.PASS_WORD)

        time.sleep(random.randint(1, 3))
        login_btn = WebDriverWait(self._driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.login_button'))
        )
        login_btn.click()

        time.sleep(random.randint(1, 3))

    def search(self, container_nos):
        if self._is_first:
            self._login()
            self._is_first = False

        # find iframe to check page is done
        WebDriverWait(self._driver, 60).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'iframe')))
        self._driver.execute_script('document.getElementById("sapUshellDashboardPage-cont").scrollTo({top: 1200});')
        track_a = WebDriverWait(self._driver, 10).until(
            EC.element_to_be_clickable(
                (
                    By.CSS_SELECTOR,
                    'a[href="https://www8.cpr.ca/cx/sap/bc/ui5_ui5/ui2/ushell/shells/abap/Fiorilaunchpad.html?'
                    'appState=lean#ZTrackAndTrace-display"]',
                )
            )
        )
        track_a.click()

        # switch to search page and search
        self._driver.switch_to.window(self._driver.window_handles[-1])

        search_input = WebDriverWait(self._driver, 75).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="search"]'))
        )
        time.sleep(5)
        search_input.send_keys(','.join(container_nos))

        # view settings button
        view_settings_btn = WebDriverWait(self._driver, 30).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[title="Settings"]'))
        )
        WebDriverWait(self._driver, 10).until(EC.invisibility_of_element((By.CSS_SELECTOR, 'div[id$=-busyIndicator]')))
        view_settings_btn.click()
        time.sleep(3)
        self._driver.execute_script('document.getElementsByClassName("sapMScrollContScroll")[0].scrollTo(0, 200);')

        # lfd checkbox
        lfd_xpath = '//td[@class="sapMListTblCell"][span[text()="Last Free Day"]]/\
                    ../td[@class="sapMListTblSelCol"]/div/div'
        WebDriverWait(self._driver, 10).until(EC.invisibility_of_element((By.CSS_SELECTOR, 'div[id$=-busyIndicator]')))

        lfd_checkbox = WebDriverWait(self._driver, 120).until( EC.presence_of_element_located((By.XPATH, lfd_xpath)) )
        try:
            lfd_checkbox.click()
        except:
            time.sleep(10)
            lfd_checkbox.click() # attempt to click again

        time.sleep(random.randint(1,3))

        ok_btn = self._driver.find_element_by_xpath('//bdi[text()="OK"]')
        ok_btn.click()

        WebDriverWait(self._driver, 60).until(self.container_no_has_value)
        return self._driver.page_source

    def container_no_has_value(self, driver):
        container_no_holder = driver.find_element_by_css_selector('div[id^="__data"] > a')
        return len(container_no_holder.text) != 0

    def get_page_source(self):
        return self._driver.page_source

    def scroll_to_next_row(self):
        scroll_bar = self._driver.find_element_by_id('__table0-vsb')
        scroll_bar.send_keys(Keys.DOWN)
        time.sleep(3)

    def quit(self):
        self._driver.quit()

