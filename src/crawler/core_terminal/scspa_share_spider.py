import time
from typing import List

import scrapy
from scrapy.http import TextResponse
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from crawler.core.selenium import ChromeContentGetter
from crawler.core_terminal.items import DebugItem, TerminalItem, InvalidContainerNoItem
from crawler.core_terminal.base_spiders import BaseMultiTerminalSpider
from crawler.core_terminal.ptp_share_spider import ContainerRoutingRule
from crawler.core_terminal.request_helpers import RequestOption
from crawler.core_terminal.rules import RuleManager, BaseRoutingRule


class ScspaShareSpider(BaseMultiTerminalSpider):
    firms_code = ""
    name = ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        rules = [
            ContainerRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)

    def start(self):
        unique_container_nos = list(self.cno_tid_map.keys())
        option = ContainerRoutingRule.build_request_option(container_no_list=unique_container_nos)
        yield self._build_request_by(option=option)

    def parse(self, response):
        yield DebugItem(info={"meta": dict(response.meta)})

        routing_rule = self._rule_manager.get_rule_by_response(response=response)

        save_name = routing_rule.get_save_name(response=response)
        self._saver.save(to=save_name, text=response.text)

        for result in routing_rule.handle(response=response):
            if isinstance(result, TerminalItem) or isinstance(result, InvalidContainerNoItem):
                c_no = result.get("container_no")
                t_ids = self.cno_tid_map.get(c_no)
                if t_ids != None:
                    for t_id in t_ids:
                        result["task_id"] = t_id
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
            return scrapy.Request(
                method=RequestOption.METHOD_GET,
                url=option.url,
                headers=option.headers,
                meta=meta,
                cookies=option.cookies,
            )
        else:
            raise RuntimeError()


class ContainerRoutingRule(BaseRoutingRule):
    name = "Container"

    @classmethod
    def build_request_option(cls, container_no_list: List[str]) -> RequestOption:
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url="https://www.google.com",
            meta={
                "container_no_list": container_no_list,
            },
        )

    def get_save_name(self, response) -> str:
        return f"{self.name}.html"

    def handle(self, response):
        getter = ContentGetter()
        content_table = getter.get(response.meta.get("container_no_list"))

        for content in content_table:
            yield TerminalItem(
                container_no=content[0],
                available=content[8],
                holds=[ele.strip() for ele in content[9].split("\\")],
                vessel=content[2],
            )


class ContentGetter(ChromeContentGetter):
    USERNAME = "tk@hardcoretech.co"
    PASSWORD = "Hardc0re"
    URL = "https://goport.scspa.com/scspa/index"

    def get(self, container_no_list):
        self.login()
        self.search(container_no_list)
        return self.extract(self._driver.page_source)

    def login(self):
        self._driver.get(self.URL)

        # login
        name_area = self._driver.find_element(By.ID, "loginId-inputEl")
        name_area.send_keys(self.USERNAME)
        passwd_area = self._driver.find_element(By.ID, "passwordId-inputEl")
        passwd_area.send_keys(self.PASSWORD)
        button = self._driver.find_element(By.XPATH, "//div[contains(@class, 'x-btn-default-large-icon')]")
        button = button.find_element(By.CSS_SELECTOR, "button")
        button.click()

    def search(self, container_no_list):
        self._to_search_page()
        self._input_search_target(container_no_list)
        WebDriverWait(self._driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//div[@id='quickInptPtrWinPnlWinId']"))
        )

    def extract(self, page_source):
        content_table = []
        response = TextResponse(
            url=self._driver.current_url,
            body=page_source,
            encoding="utf-8",
        )

        table = response.xpath("(//table[contains(@class, 'x-grid-table')])[2]")
        tr_list = table.xpath("./tbody/tr")[1:]
        for tr in tr_list:
            content = [ele.strip() for ele in tr.xpath("./td/div/text()").getall()]
            content_table.append(tr.xpath("./td/div/text()").getall())

        return content_table

    def _to_search_page(self):
        WebDriverWait(self._driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//a[@class='x-menu-item-link']"))
        )
        reports = self._driver.find_element(By.XPATH, "//a[text()='REPORTS']")
        reports.click()
        time.sleep(1)  # wait for website
        quick_reports = self._driver.find_element(By.XPATH, "//a[@class='x-menu-item-link']")
        quick_reports.click()

        # toggle folders and finally click 'Track Imports by Container WT NC'
        list_tree = self._driver.find_element(By.XPATH, "//div[@id='queryListingeTreeGridId-body']")
        time.sleep(1)  # wait for website
        folder_toggler = list_tree.find_element(By.XPATH, "//tr[2]/td/div/img[contains(@class, 'x-tree-expander')]")
        folder_toggler.click()
        time.sleep(1)  # wait for website
        folder_toggler = list_tree.find_element(By.XPATH, "//tr[3]/td/div/img[contains(@class, 'x-tree-expander')]")
        folder_toggler.click()
        time.sleep(1)  # wait for website
        leaf = list_tree.find_element(By.XPATH, "//div[text()='Track Imports by Container WT NC']")
        leaf.click()
        time.sleep(1)  # wait for website

    def _input_search_target(self, container_no_list):
        textarea = self._driver.find_element(By.XPATH, "//textarea")
        textarea.send_keys("\n".join(container_no_list))
        button = self._driver.find_element(By.XPATH, "//button[contains(@id, 'scspabutton-')]")
        button.click()
        time.sleep(1)  # wait for website
