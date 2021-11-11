from typing import Dict

import scrapy
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

from crawler.core_terminal.base import TERMINAL_RESULT_STATUS_FATAL
from crawler.core_terminal.base_spiders import BaseMultiTerminalSpider
from crawler.core_terminal.items import (
    DebugItem,
    TerminalItem,
    ExportErrorData,
    InvalidContainerNoItem,
)
from crawler.core_terminal.request_helpers import RequestOption
from crawler.core_terminal.rules import RuleManager, BaseRoutingRule
from crawler.core.selenium import ChromeContentGetter

BASE_URL = "http://mca.poha.com/container-availability"


class PohaShareSpider(BaseMultiTerminalSpider):
    firms_code = ""
    name = ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        rules = [
            ConfigureSettingsRule(),
            ContainerRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)

    def start(self):
        option = ConfigureSettingsRule.build_request_option(task_ids=self.task_ids, container_nos=self.container_nos)
        yield self._build_request_by(option=option)

    def parse(self, response):
        yield DebugItem(info={"meta": dict(response.meta)})

        routing_rule = self._rule_manager.get_rule_by_response(response=response)

        save_name = routing_rule.get_save_name(response=response)
        self._saver.save(to=save_name, text=response.text)

        for result in routing_rule.handle(response=response):
            if True in [isinstance(result, item) for item in [TerminalItem, InvalidContainerNoItem, ExportErrorData]]:
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
                method="GET",
                url=option.url,
                headers=option.headers,
                meta=meta,
                cookies=option.cookies,
            )
        else:
            raise RuntimeError()


# -------------------------------------------------------------------------------


class ConfigureSettingsRule(BaseRoutingRule):
    name = "Configure"

    @classmethod
    def build_request_option(cls, task_ids, container_nos) -> RequestOption:
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url="https://www.google.com",
            meta={"task_ids": task_ids, "container_nos": container_nos},
        )

    def get_save_name(self, response) -> str:
        return f"{self.name}.json"

    def handle(self, response):
        task_ids = response.meta.get("task_ids")
        container_nos = response.meta.get("container_nos")

        browser = ContentGetter()
        browser.configure()
        cookies = browser.get_cookies_dict()
        browser.close()

        for task_id, container_no in zip(task_ids, container_nos):
            yield ContainerRoutingRule.build_request_option(task_id=task_id, container_no=container_no, cookies=cookies)


# -------------------------------------------------------------------------------


class ContainerRoutingRule(BaseRoutingRule):
    name = "Container"

    @classmethod
    def build_request_option(cls, task_id, container_no, cookies: Dict) -> RequestOption:
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=f"{BASE_URL}-details?number={container_no}",
            cookies=cookies,
            meta={"task_id": task_id, "container_no": container_no},
        )

    def get_save_name(self, response) -> str:
        return f"{self.name}.json"

    def handle(self, response):
        container_no = response.xpath("//span[@id='MainContent_EQUIPMENTNBR']/text()").get()
        if container_no:
            info = {}

            info["Available"] = response.css("div[id^='MainContent_pnl']").css("span::text").get()
            info["Container #"] = container_no
            info["Line Status"] = response.xpath("//span[@id='MainContent_FREIGHT']/text()").get()
            info["Customs Status"] = response.xpath("//span[@id='MainContent_CUSTOMS']/text()").get()
            info["VGM"] = response.xpath("//span[@id='MainContent_VGM']/text()").get()
            info["Holds"] = response.xpath("//span[@id='MainContent_HOLDS']/text()").get()
            info["Shipping Line"] = response.xpath("//span[@id='MainContent_SHIPPINGLINE']/text()").get()
            info["Size/Type/Height"] = response.xpath("//span[@id='MainContent_SIZETYPEHEIGHT']/text()").get()

            if info.get("Container #") == response.meta.get("container_no"):
                yield TerminalItem(
                    task_id=response.meta.get("task_id"),
                    container_no=info.get("Container #"),
                    available=info.get("Available").strip(),
                    carrier_release=info.get("Line Status"),
                    customs_release=info.get("Customs Status"),
                    weight=info.get("VGM"),
                    holds=info.get("Holds"),
                    carrier=info.get("Shipping Line"),
                    container_spec=info.get("Size/Type/Height"),
                )
            else:
                yield ExportErrorData(
                    status=TERMINAL_RESULT_STATUS_FATAL,
                    detail="Target container_no does not meet the container_no that website shows",
                )
        else:
            yield InvalidContainerNoItem(
                task_id=response.meta.get("task_id"),
                container_no=response.meta.get("container_no"),
            )


# -------------------------------------------------------------------------------


class ContentGetter(ChromeContentGetter):
    def configure(self):
        self._driver.get(f"{BASE_URL}")

        terminal_select = Select(self._driver.find_element(By.XPATH, "//select[@id='ddlTerminal']"))
        terminal_select.select_by_value("BarboursCut")
        language_select = Select(self._driver.find_element(By.XPATH, "//select[@id='ddlSelLanguage']"))
        language_select.select_by_value("en")
        self._driver.find_element(By.XPATH, "//div[@class='ui-dialog-buttonset']/button").click()
