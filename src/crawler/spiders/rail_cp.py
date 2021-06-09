import random
import time

import scrapy

from crawler.core_rail.base_spiders import BaseMultiRailSpider
from crawler.core_rail.exceptions import DriverMaxRetryError
from crawler.core_rail.items import BaseRailItem, RailItem, DebugItem, InvalidContainerNoItem
from crawler.core_rail.request_helpers import RequestOption
from crawler.core_rail.rules import RuleManager, BaseRoutingRule
from crawler.extractors.table_cell_extractors import BaseTableCellExtractor, FirstTextTdExtractor
from crawler.extractors.table_extractors import TableExtractor, TopHeaderTableLocator
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
            c_no_wiout_check_code = c_no[:10]
            c_no_info = container_infos[c_no_wiout_check_code]

            if c_no_info['last_reported'] == 'No information found matching the specified criteria':
                yield InvalidContainerNoItem(container_no=c_no)
                continue

            yield RailItem(
                container_no=c_no,
                current_location=c_no_info['current_location'],
                status=c_no_info['equipment_status'],
                grounded=c_no_info['grounded'],
                last_event_location=c_no_info['last_event_location'],
                last_event_time=c_no_info['last_event_time'],
                lfd=c_no_info['lfd'],
                hold=c_no_info['holds'],
                eta=c_no_info['eta'],
                ata=c_no_info['ata'],
            )

    @staticmethod
    def _extract_container_infos(response: scrapy.Selector):
        container_no_table = response.css('table#__table8-table-fixed') # use xpath instead
        container_no_table_locator = TopHeaderTableLocator()
        container_no_table_locator.parse(table=container_no_table)
        container_no_table_extractor = TableExtractor(table_locator=container_no_table_locator)

        container_info_table = response.css('table#rowTable')
        container_info_table_locator = TopHeaderTableLocator()
        container_info_table_locator.parse(table=container_info_table)
        container_info_table_extractor = TableExtractor(table_locator=container_info_table_locator)

        container_infos = {}
        for left in container_no_table_locator.iter_left_header():
            c_no_and_spec = container_no_table_extractor.extract_cell(
                top='Equipment', left=left, extractor=ContainerNoSpecCellExtractor()
            )
            container_no = c_no_and_spec['container_no']

            xtd = container_info_table_extractor.extract_cell(top='Act Arrival', left=left, extractor=ArrivalCellExtractor())
            eta = xtd['eta']
            ata = xtd['ata']

            holds_in_span = container_info_table_extractor.extract_cell(
                top='Holds', left=left, extractor=FirstTextTdExtractor(css_query='span::text')
            )
            holds = container_info_table_extractor.extract_cell(top='Holds', left=left)

            container_infos[container_no] = {
                'current_location': container_info_table_extractor.extract_cell(top='Current Position', left=left),
                'last_reported': container_info_table_extractor.extract_cell(top='Last Reported', left=left),
                'equipment_status': container_info_table_extractor.extract_cell(top='Equipment Status', left=left),
                'load_status':container_info_table_extractor.extract_cell(top='', left=left),
                'grounded': container_info_table_extractor.extract_cell(top='Grounded', left=left),
                'eta': eta,
                'ata': ata,
                'holds': holds or holds_in_span,
                'last_free_day': container_info_table_extractor.extract_cell(top='Last Free Day', left=left),
            }

        return container_infos


class ContainerNoSpecCellExtractor(BaseTableCellExtractor):
    def extract(self, cell: scrapy.Selector):
        all_texts = cell.css('::text').getall()
        raw_container_no = all_texts[1]  # ex: BEAU 0000455397
        prefix, numbers = raw_container_no.split(' ')
        container_no = prefix + numbers[4:]

        spec = None if len(all_texts) != 3 else all_texts[2].strip()

        return {
            'container_no': container_no,
            'spec': spec,
        }


class ArrivalCellExtractor(BaseTableCellExtractor):
    def extract(self, cell: scrapy.Selector):
        i_text = cell.css('i::text').get()
        first_text = cell.css('::text').get()

        if isinstance(i_text, str):
            eta = i_text[1:-1]
            ata = ''
        elif isinstance(first_text, str):
            eta = ''
            ata = first_text.strip()
        else:
            eta = ''
            ata = ''

        return {'eta': eta, 'ata': ata}


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
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)

        self._driver = webdriver.Chrome(options=options)
        self._driver.get('https://www8.cpr.ca/f5idp/saml/idp/profile/redirectorpost/sso')
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

        # view settings button
        view_settings_btn = WebDriverWait(self._driver, 30).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[title="Settings"]'))
        )
        view_settings_btn.click()
        time.sleep(random.randint(1,3))

        # lfd checkbox
        lfd_xpath = '//td[@class="sapMListTblCell"][span[text()="Last Free Day"]]/\
                    ../td[@class="sapMListTblSelCol"]/div/div/input'

        lfd_checkbox = WebDriverWait(self._driver, 60).until( EC.presence_of_element_located((By.XPATH, lfd_xpath)) )

        # print('================================')
        # print(lfd_checkbox.get_attribute('innerHTML'))
        WebDriverWait(self._driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, lfd_xpath)))
        lfd_checkbox.click()
        time.sleep(random.randint(1,3))

        ok_btn = self._driver.find_element_by_xpath('//bdi[text()="OK"]')
        ok_btn.click()
        time.sleep(5)

        search_input.send_keys(','.join(container_nos))
        return self._driver.page_source

    def quit(self):
        self._driver.quit()
