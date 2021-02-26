import json
import time
from typing import List

from scrapy import Request, FormRequest, Selector
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from crawler.core_terminal.base_spiders import BaseMultiSearchTerminalSpider
from crawler.core_terminal.exceptions import LoadWebsiteTimeOutFatal
from crawler.core_terminal.items import (
    BaseTerminalItem, DebugItem, TerminalItem, InvalidContainerNoItem
)
from crawler.core_terminal.rules import RuleManager, BaseRoutingRule, RequestOption
from crawler.extractors.selector_finder import BaseMatchRule, find_selector_from
from crawler.extractors.table_extractors import BaseTableLocator, HeaderMismatchError, TableExtractor

BASE_URL = 'https://apps.maherterminals.com'


class MaherContentGetter:
    USER_NAME = 'hard202006010'
    PASS_WORD = 'hardc0re'

    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--disable-extensions')
        # options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument('--window-size=1920,1080')

        self.driver = webdriver.Chrome(options=options)
        self._is_first = True

    def search_and_return(self, container_no):
        if self._is_first:
            self._is_first = False
            self._login_and_go_to_search_page()

        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "textarea[name='equipment']"))
            )
        except TimeoutException:
            raise LoadWebsiteTimeOutFatal()

        container_inquiry_text_area = self.driver.find_element_by_css_selector("textarea[name='equipment']")
        container_inquiry_text_area.clear()
        container_inquiry_text_area.send_keys(container_no)

        search_btn = self.driver.find_element_by_css_selector("input[onclick='Search();']")
        search_btn.click()

        time.sleep(3)
        return self.driver.page_source

    def _login_and_go_to_search_page(self):
        self.driver.get('https://apps.maherterminals.com/csp/loginAction.do?method=login')

        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='userBean.username']"))
            )
        except TimeoutException:
            raise LoadWebsiteTimeOutFatal()

        user_name_input = self.driver.find_element_by_css_selector("input[name='userBean.username']")
        pass_word_input = self.driver.find_element_by_css_selector("input[name='userBean.password']")

        user_name_input.send_keys(self.USER_NAME)
        pass_word_input.send_keys(self.PASS_WORD)

        login_btn = self.driver.find_element_by_css_selector("input[name='cancelButton']")
        login_btn.click()

        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div#lnk4"))
            )
        except TimeoutException:
            raise LoadWebsiteTimeOutFatal()

        equipment_btn = self.driver.find_element_by_css_selector('div#lnk4')
        ActionChains(driver=self.driver).move_to_element(equipment_btn).perform()

        time.sleep(0.5)

        inquiry_btn = self.driver.find_element_by_css_selector('div#lnk18')
        ActionChains(driver=self.driver).move_to_element(inquiry_btn).perform()

        time.sleep(0.5)

        container_inquiry_btn = self.driver.find_element_by_css_selector('a#lnk20')
        ActionChains(driver=self.driver).move_to_element(container_inquiry_btn).click().perform()

    def quit(self):
        self.driver.quit()


class TerminalMaherMultiSpider(BaseMultiSearchTerminalSpider):
    name = 'terminal_maher_multi'

    def __init__(self, *args, **kwargs):
        super(TerminalMaherMultiSpider, self).__init__(*args, **kwargs)

        rules = [
            SearchRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)

    def start(self):
        option = SearchRoutingRule.build_request_option(container_no_list=self.container_no_list)
        yield self._build_request_by(option=option)

    def parse(self, response):
        yield DebugItem(info={'meta': dict(response.meta)})

        routing_rule = self._rule_manager.get_rule_by_response(response=response)

        save_name = routing_rule.get_save_name(response=response)
        self._saver.save(to=save_name, text=response.text)

        for result in routing_rule.handle(response=response):
            if isinstance(result, BaseTerminalItem):
                yield result
            elif isinstance(result, RequestOption):
                yield self._build_request_by(option=result)
            else:
                raise RuntimeError()

    def _build_request_by(self, option: RequestOption):
        meta = {
            RuleManager.META_TERMINAL_CORE_RULE_NAME: option.rule_name,
            **option.meta,
        }

        if option.method == RequestOption.METHOD_GET:
            return Request(
                url=option.url,
                headers=option.headers,
                meta=meta,
                dont_filter=True,
            )
        elif option.method == RequestOption.METHOD_POST_FORM:
            return FormRequest(
                url=option.url,
                formdata=option.form_data,
                headers=option.headers,
                meta=meta,
                dont_filter=True,
            )
        elif option.method == RequestOption.METHOD_POST_BODY:
            return Request(
                url=option.url,
                headers=option.headers,
                body=option.body,
                meta=meta,
                dont_filter=True,
                method='POST',
            )
        else:
            raise ValueError(f'Invalid option.method [{option.method}]')


# -------------------------------------------------------------------------------


class SearchRoutingRule(BaseRoutingRule):
    name = 'SEARCH'

    @classmethod
    def build_request_option(cls, container_no_list: List[str]) -> RequestOption:
        url = 'https://www.google.com'

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=url,
            meta={
                'container_no_list': container_no_list,
            },
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.html'

    def handle(self, response):
        container_no_list = response.meta['container_no_list']

        content_getter = MaherContentGetter()

        for container_no in container_no_list:
            response_text = content_getter.search_and_return(container_no=container_no)
            response = Selector(text=response_text)

            if self._is_container_no_invalid(response=response):
                yield InvalidContainerNoItem(container_no=container_no)
                return

            container_info = self.extract_container_info(response=response)
            yield TerminalItem(
                **container_info
            )

    @staticmethod
    def _is_container_no_invalid(response: Selector) -> bool:
        tables = response.css('table')
        rule = SpecificClassTdContainTextMatchRule(td_class='clsBlackBold', text='Not On File')
        return bool(find_selector_from(selectors=tables, rule=rule))

    @staticmethod
    def extract_container_info(response: Selector):
        tables = response.css('table')
        rule = SpecificClassTdContainTextMatchRule(td_class='clsRedSubHeading', text='Equipment Status')

        table = find_selector_from(selectors=tables, rule=rule)
        table_locator = MaherLeftHeadTableLocator()
        table_locator.parse(table=table)
        table_extractor = TableExtractor(table_locator=table_locator)

        return {
            'container_no': table_extractor.extract_cell(left='Container', top=None),
            'container_spec': table_extractor.extract_cell(left='LHT', top=None),
            'weight': table_extractor.extract_cell(left='Gross Weight', top=None),
            'holds': table_extractor.extract_cell(left='Holds', top=None),
            'hazardous': table_extractor.extract_cell(left='Hazards', top=None),
            'cy_location': table_extractor.extract_cell(left='Location Type', top=None),
            'vessel': table_extractor.extract_cell(left='Vessel', top=None),
            'voyage': table_extractor.extract_cell(left='Voyage', top=None),
        }


# -------------------------------------------------------------------------------


class SpecificClassTdContainTextMatchRule(BaseMatchRule):

    def __init__(self, td_class: str, text: str):
        self._td_class = td_class
        self._text = text

    def check(self, selector: Selector) -> bool:
        sub_headings = (
                selector.xpath(f'./tbody/tr/td[@class="{self._td_class}"]') or
                selector.xpath(f'./tr/td[@class="{self._td_class}"]')
        )

        for sub_heading in sub_headings:
            sub_heading_text = sub_heading.css('::text').get().strip()
            if self._text in sub_heading_text:
                return True

        return False


class MaherLeftHeadTableLocator(BaseTableLocator):
    def __init__(self):
        self._td_map = {}  # title: data_td

    def parse(self, table: Selector):
        trs = table.css('tr')

        for tr in trs:
            if tr.css('td.clsRedSubHeading'):
                continue

            titles = tr.css('td.clsBlackBold::text').getall()
            titles = [title.strip()[:-1] for title in titles]
            data_tds = tr.css('td.clsBlack')

            for title, data_td in zip(titles, data_tds):
                self._td_map[title] = data_td

    def get_cell(self, left, top=None) -> Selector:
        assert top is None
        try:
            return self._td_map[left]
        except KeyError as err:
            raise HeaderMismatchError(repr(err))

    def has_header(self, top=None, left=None) -> bool:
        assert top is None
        return bool(self._td_map.get(left))

