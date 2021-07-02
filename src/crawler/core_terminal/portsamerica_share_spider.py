import dataclasses
from typing import Dict, List
import time
import re

import scrapy
from scrapy import Selector
from selenium import webdriver

from crawler.core_terminal.base_spiders import BaseMultiTerminalSpider
from crawler.core_terminal.items import DebugItem, TerminalItem, InvalidContainerNoItem
from crawler.core_terminal.request_helpers import RequestOption
from crawler.core_terminal.rules import RuleManager, BaseRoutingRule
from crawler.extractors.table_extractors import BaseTableLocator, HeaderMismatchError

BASE_URL = 'https://voyagertrack.portsamerica.com'


@dataclasses.dataclass
class CompanyInfo:
    site_name: str
    upper_short: str
    email: str
    password: str


@dataclasses.dataclass
class WarningMessage:
    msg: str


class PortsamericaShareSpider(BaseMultiTerminalSpider):
    name = ''
    company_info = CompanyInfo(
        site_name='',
        upper_short='',
        email='',
        password='',
    )

    def __init__(self, *args, **kwargs):
        super(PortsamericaShareSpider, self).__init__(*args, **kwargs)

        rules = [SearchContainerRule()]

        self._rule_manager = RuleManager(rules=rules)

    def start(self):
        unique_container_nos = list(self.cno_tid_map.keys())
        request_option = SearchContainerRule.build_request_option(
            container_no_list=unique_container_nos, company_info=self.company_info
        )
        yield self._build_request_by(option=request_option)

    def parse(self, response):
        yield DebugItem(info={'meta': dict(response.meta)})

        routing_rule = self._rule_manager.get_rule_by_response(response=response)

        save_name = routing_rule.get_save_name(response=response)
        self._saver.save(to=save_name, text=response.text)

        for result in routing_rule.handle(response=response):
            if isinstance(result, TerminalItem) or isinstance(result, InvalidContainerNoItem):
                c_no = result['container_no']
                t_ids = self.cno_tid_map[c_no]
                for t_id in t_ids:
                    result['task_id'] = t_id
                    yield result
            elif isinstance(result, RequestOption):
                yield self._build_request_by(option=result)
            elif isinstance(result, WarningMessage):
                self.logger.warning(msg=result.msg)
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
            raise RuntimeError()


class SearchContainerRule(BaseRoutingRule):
    name = 'SEARCH'

    @classmethod
    def build_request_option(cls, container_no_list: List, company_info: CompanyInfo) -> RequestOption:
        url = 'https://google.com'
        return RequestOption(
            method=RequestOption.METHOD_GET,
            rule_name=cls.name,
            url=url,
            meta={'container_no_list': container_no_list, 'company_info': company_info},
        )

    def handle(self, response):
        company_info = response.meta['company_info']
        container_no_list = response.meta['container_no_list']

        content_getter = ContentGetter()
        content_getter.login(company_info.email, company_info.password, company_info.site_name)
        resp = content_getter.search(container_no_list)

        containers = content_getter.get_container_info(Selector(text=resp), len(container_no_list))
        content_getter.quit()

        for container in containers:
            yield TerminalItem(
                **container,
            )


class ContentGetter:
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
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)

        self._driver = webdriver.Chrome(options=options)

    def login(self, username, password, site_name):
        url = f'{BASE_URL}/logon?siteId={site_name}'
        self._driver.get(url)
        time.sleep(5)
        username_input = self._driver.find_element_by_xpath('//*[@id="UserName"]')
        username_input.send_keys(username)
        time.sleep(2)
        password_input = self._driver.find_element_by_xpath('//*[@id="Password"]')
        password_input.send_keys(password)
        time.sleep(2)
        login_btn = self._driver.find_element_by_xpath('//*[@id="btnLogonSubmit"]')
        login_btn.click()
        time.sleep(10)

    def search(self, container_no_list):
        url = f'{self._driver.current_url}#/Report/ImportContainer'
        self._driver.get(url)
        time.sleep(5)

        multi_search_btn = self._driver.find_element_by_xpath('//*[@id="imgOpenContainerMultipleEntryDialog"]')
        multi_search_btn.click()
        time.sleep(3)

        container_text_area = self._driver.find_element_by_xpath('//*[@id="ContainerNumbers"]')
        container_text_area.send_keys('\n'.join(container_no_list))

        time.sleep(3)
        search_btn = self._driver.find_element_by_xpath('//*[@id="btnContainerSubmitMulti"]')
        search_btn.click()
        time.sleep(8)

        return self._driver.page_source

    def get_container_info(self, resp: Selector, numbers: int):
        # table = resp.xpath('//*[@id="divImportContainerGridPanel"]/div[1]/table')
        # table_locator = TableLocator()
        # table_locator.parse(table=table, numbers=numbers)

        res = []
        tds = resp.xpath('//*[@id="divImportContainerGridPanel"]/div[1]/table/tbody/tr/td')
        for i in range(int(len(tds) / 17)):
            appointment_date = ''.join(tds[i * 17 + 5].xpath('.//text()').extract())
            gate_out_date = ''.join(tds[i * 17 + 3].xpath('.//text()').extract()).strip()

            if re.search('([0-9]+/[0-9]+/[0-9]{4}[0-9]{4}-[0-9]{4})', appointment_date):
                date_split_list = appointment_date.split('/')
                time_split_list = date_split_list[-1][4:].split('-')
                date_split_list[-1] = date_split_list[-1][:4]
                appointment_date = '/'.join(date_split_list) + ' ' + time_split_list[0]

            if re.search('([0-9]+/[0-9]+/[0-9]{4} [0-9]+:[0-9]{2})', gate_out_date):
                date_split_list = gate_out_date.split('\n')
                gate_out_date = date_split_list[-1]

            res.append(
                {
                    'container_no': ''.join(tds[i * 17 + 1].xpath('.//text()').extract()).strip().replace('-', ''),
                    'ready_for_pick_up': ''.join(tds[i * 17 + 2].xpath('.//text()').extract()).strip(),
                    'gate_out_date': gate_out_date,
                    'appointment_date': appointment_date.strip(),
                    'customs_release': ''.join(tds[i * 17 + 6].xpath('.//text()').extract()).strip(),
                    'freight_release': ''.join(tds[i * 17 + 7].xpath('.//text()').extract()).strip(),
                    'carrier_release': ''.join(tds[i * 17 + 7].xpath('.//text()').extract()).strip(),
                    'holds': ''.join(tds[i * 17 + 9].xpath('.//text()').extract()).strip(),
                    'demurrage': ''.join(tds[i * 17 + 11].xpath('.//text()').extract()).strip(),
                    'last_free_day': ''.join(tds[i * 17 + 12].xpath('.//text()').extract()).strip(),
                    'carrier': ''.join(tds[i * 17 + 13].xpath('.//text()').extract()).strip(),
                    'container_spec': ''.join(tds[i * 17 + 14].xpath('.//text()').extract()).strip(),
                }
            )

        return res

    def quit(self):
        self._driver.quit()


class TableLocator(BaseTableLocator):
    def __init__(self):
        self._td_map = []

    def parse(self, table: Selector, numbers: int = 1):
        titles = self._get_titles(table)

    def _get_titles(self, table: Selector):
        titles = table.css('th::text').getall()
        return [title.strip() for title in titles]

    def get_cell(self, left, top=None) -> Selector:
        try:
            return self._td_map[left][top]
        except (KeyError, IndexError) as err:
            raise HeaderMismatchError(repr(err))
