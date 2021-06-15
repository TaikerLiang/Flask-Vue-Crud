import random
import time

import scrapy
from scrapy import Selector

from crawler.core_rail.base_spiders import BaseMultiRailSpider
from crawler.core_rail.exceptions import DriverMaxRetryError
from crawler.core_rail.items import BaseRailItem, RailItem, DebugItem, InvalidContainerNoItem
from crawler.core_rail.request_helpers import RequestOption
from crawler.core_rail.rules import RuleManager, BaseRoutingRule
from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
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

        container_infos = self._extract_container_infos(response=response)

        for c_no in container_nos:
            info = container_infos[c_no]

            if info['last_event'] == '':
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
    def _extract_container_infos(response: scrapy.Selector):
        container_no_header_table = response.css('table[id$=header-fixed-fixrow]') # header table (container_no)
        container_no_content_table = response.css('div > table[id$=-table-fixed]') # content table (container_no)
        container_info_header_table = response.css('div.sapUiTableCtrlScr > table') # header table (container_info)
        container_info_content_table = response.css('div.sapUiTableCtrlCnt > table[id$=-table]') # content table (container_info)

        container_no_table_parser = ContainerNoTableParser()
        container_no_table_parser.parse(header_table=container_no_header_table,
                                        content_table=container_no_content_table)
        container_no_results = container_no_table_parser.get()

        container_info_table_parser = ContainerInfoTableParser()
        container_info_table_parser.parse(header_table=container_info_header_table,
                                          content_table=container_info_content_table,
                                          rows=len(container_no_results))
        container_info_results = container_info_table_parser.get()

        container_infos = {}
        for container_info in zip(container_no_results, container_info_results):
            container_info = dict(container_info[0], **container_info[1])

            container_no = container_info['Equipment']
            last_reported = container_info['Last Reported Station'].split()[1:]
            last_event_location = ' '.join(last_reported[:-1])

            last_event_time = last_reported[-1]
            last_event = container_info['Equipment Status'] + ', ' + container_info['Load Status']
            xta = container_info['ETA'].split('\n')

            head, value = xta[0], xta[1]
            eta = value if head == 'ETA' else ''
            ata = value if head == 'Arrived on' else ''

            container_infos[container_no] = {
                'last_event_location': last_event_location,
                'last_event_time': last_event_time,
                'last_event': last_event,
                'eta': eta,
                'ata': ata,
                'last_free_day': container_info['Last Free Day'],
            }

        return container_infos


class ContainerNoTableParser:
    def __init__(self):
        self._items = []

    def parse(self, header_table: Selector, content_table: Selector):
        headers = header_table.css('tbody > tr > td')
        container_no_header = headers[1].css('span::text').get().strip()

        for tr in content_table.css('tbody > tr'):
            td = tr.css('td')[1]
            container_no = td.css('a::text').get()
            if container_no:
                self._items.append({container_no_header: container_no})
            else:
                return

    def get(self):
        return self._items


class ContainerInfoTableParser:
    def __init__(self):
        self._items = []
        self._header_set = {
            'Last Reported Station',
            'Equipment Status',
            'Load Status',
            'ETA',
            'Last Free Day',
        }

    def parse(self, header_table: Selector, content_table: Selector, rows):
        headers = header_table.css('tbody > tr > td span::text').getall()

        for tr in content_table.css('tbody > tr')[:rows]:
            content_list = self.get_content_list(tr=tr)

            info_dict = {}
            for i, content in enumerate(content_list):
                header = headers[i]
                if header in self._header_set:
                    info_dict[header] = content

            self._items.append(info_dict)

    def get_content_list(self, tr: Selector):
        content_list = []
        for td in tr.css('td')[:-1]:
            content = td.css('div>span::text').get()
            content_list.append(content)

        return content_list

    def get(self):
        return self._items


class ContentGetter:
    USER_NAME = 'gftracking'
    PASS_WORD = 'GoFreight2021'

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

    def quit(self):
        self._driver.quit()

