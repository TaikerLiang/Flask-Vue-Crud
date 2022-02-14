import time
from typing import List

import scrapy
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from crawler.core.selenium import ChromeContentGetter
from crawler.core_terminal.items import DebugItem, TerminalItem
from crawler.core_terminal.base_spiders import BaseMultiTerminalSpider
from crawler.core_terminal.request_helpers import RequestOption
from crawler.core_terminal.rules import RuleManager, BaseRoutingRule

MAX_PAGE_NUM = 10


class ScspaShareSpider(BaseMultiTerminalSpider):
    firms_code = ""
    name = ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.custom_settings.update({"CONCURRENT_REQUESTS": "1"})

        self._content_getter = ContentGetter(proxy_manager=None, is_headless=True)

        rules = [
            ContainerRoutingRule(content_getter=self._content_getter),
            NextRoundRoutingRule(),
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
            if isinstance(result, TerminalItem):
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
                dont_filter=True,
            )
        else:
            raise RuntimeError()


class ContainerRoutingRule(BaseRoutingRule):
    name = "Container"

    def __init__(self, content_getter: ChromeContentGetter):
        self._content_getter = content_getter

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
        container_no_list = response.meta["container_no_list"]
        res = self._content_getter._search_and_return(container_no_list=container_no_list[:MAX_PAGE_NUM])

        for item in self._handle_response(response=res):
            yield item

        yield NextRoundRoutingRule.build_request_option(container_no_list)

    @classmethod
    def _handle_response(cls, response):
        content_table = cls._extract_content_table(response)
        for content in content_table:
            yield TerminalItem(
                container_no=content[0],
                available=content[8],
                holds=[ele.strip() for ele in content[9].split("\\")],
                vessel=content[2],
            )

    @staticmethod
    def _extract_content_table(page_source):
        content_table = []
        response = scrapy.Selector(text=page_source)

        table = response.xpath("(//table[contains(@class, 'x-grid-table')])[2]")
        tr_list = table.xpath("./tbody/tr")[1:]
        for tr in tr_list:
            content_table.append(tr.xpath("./td/div/text()").getall())

        return content_table


class NextRoundRoutingRule(BaseRoutingRule):
    @classmethod
    def build_request_option(cls, container_no_list: List[str]) -> RequestOption:
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url="https://eval.edi.hardcoretech.co/c/livez",
            meta={"container_no_list": container_no_list},
        )

    def handle(self, response):
        container_no_list = response.meta["container_no_list"]

        if len(container_no_list) <= MAX_PAGE_NUM:
            return

        container_no_list = container_no_list[MAX_PAGE_NUM:]

        yield ContainerRoutingRule.build_request_option(container_no_list=container_no_list)


class ContentGetter(ChromeContentGetter):
    USERNAME = "tk@hardcoretech.co"
    PASSWORD = "Goft@220126"
    URL = "https://goport.scspa.com/scspa/index"

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

    def _search_and_return(self, container_no_list):
        if self._is_first:
            self.login()
            self._close_popup()
            self._to_search_page()
            self._is_first = False
        else:
            self._back_to_search_page()

        self._input_search_target(container_no_list)

        # check the result popup is appeared
        WebDriverWait(self._driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//div[@id='quickInptPtrWinPnlWinId']"))
        )
        return self.get_page_source()

    def _close_popup(self):
        while True:
            try:
                self._driver.find_element(By.XPATH, "//div[id='tosModelPopUpWinId']")
            except:
                break
            else:
                close_button = self._driver.find_element(
                    By.XPATH, "//button[id='agreeTermsAndServiceOKButtonId-btnEl']"
                )
                close_button.click()

    def _to_search_page(self):
        WebDriverWait(self._driver, 60).until(
            EC.presence_of_element_located((By.XPATH, "//a[@class='x-menu-item-link']"))
        )
        reports = self._driver.find_element(By.XPATH, "//a[text()='REPORTS']")
        reports.click()
        time.sleep(1)  # wait for website
        quick_reports = self._driver.find_element(By.XPATH, "//a[@class='x-menu-item-link']")
        quick_reports.click()
        time.sleep(1)  # wait for website

        # toggle folders and finally click 'Track Imports by Container WT NC'
        WebDriverWait(self._driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//div[@id='queryListingeTreeGridId-body']"))
        )
        list_tree = self._driver.find_element(By.XPATH, "//div[@id='queryListingeTreeGridId-body']")
        WebDriverWait(self._driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//tr[2]/td/div/img[contains(@class, 'x-tree-expander')]"))
        )
        folder_toggler = list_tree.find_element(By.XPATH, "//tr[2]/td/div/img[contains(@class, 'x-tree-expander')]")
        folder_toggler.click()
        time.sleep(1)  # wait for website
        WebDriverWait(self._driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//img[@class='x-tree-elbow-line']"))
        )
        folder_toggler = list_tree.find_element(
            By.XPATH, "//img[@class='x-tree-elbow-line']/following-sibling::img[contains(@class, 'x-tree-expander')]"
        )
        folder_toggler.click()
        time.sleep(1)  # wait for website
        WebDriverWait(self._driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//div[text()='Track Imports by Container WT NC']"))
        )
        leaf = list_tree.find_element(By.XPATH, "//div[text()='Track Imports by Container WT NC']")
        leaf.click()
        time.sleep(1)  # wait for website

    def _input_search_target(self, container_no_list):
        WebDriverWait(self._driver, 20).until(EC.presence_of_element_located((By.XPATH, "//textarea")))
        textarea = self._driver.find_element(By.XPATH, "//textarea")
        textarea.send_keys("\n".join(container_no_list))
        button = self._driver.find_element(By.XPATH, "//button[contains(@id, 'scspabutton-')]")
        button.click()
        time.sleep(1)  # wait for website

    def _back_to_search_page(self):
        button = self._driver.find_element(
            By.XPATH, "//div[@id='quickInptPtrWinPnlWinId_header-targetEl']/div/img[contains(@class, 'x-tool-close')]"
        )
        button.click()
        time.sleep(1)
        clear_button = self._driver.find_element(By.XPATH, "//button[span[contains(@class, 'clearIcon')]]")
        clear_button.click()
        time.sleep(1)
