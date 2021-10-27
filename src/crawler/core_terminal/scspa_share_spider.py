from typing import List


from selenium import webdriver

from crawler.core_terminal.base_spiders import BaseMultiTerminalSpider
from crawler.core_terminal.items import DebugItem, TerminalItem, InvalidContainerNoItem
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
        driver = webdriver.Chrome("chromedriver")
        driver.get("https://goport.scspa.com/scspa/index")
        name_area = driver.find_element_by_id("loginId-inputEl")
        name_area.send_keys("tk@hardcoretech.co")
        passwd_area = driver.find_element_by_id("passwordId-inputEl")
        passwd_area.send_keys("Hardc0re")
        button = driver.find_element_by_xpath("//div[contains(@class, 'x-btn-default-large-icon')]")
        button = button.find_element_by_css_selector("button")
        button.click()

        reports = driver.find_element_by_xpath("//a[@class='x-menu-item-link']")
        reports.click()

        list_tree = driver.find_element_by_xpath("//div[@id='queryListingeTreeGridId-body']")
        folder_toggler = list_tree.find_element_by_xpath("//tr[2]/td/div/img[contains(@class, 'x-tree-expander')]")
        folder_toggler.click()
        folder_toggler = list_tree.find_element_by_xpath("//tr[3]/td/div/img[contains(@class, 'x-tree-expander')]")
        folder_toggler.click()
        leaf = list_tree.find_element_by_xpath("//div[text()='Track Imports by Container WT NC']")
        leaf.click()

        textarea = driver.find_element_by_xpath("//textarea")
        textarea.send_keys("HAMU1028917")

        button = driver.find_element_by_xpath("//button[@id='scspabutton-1178-btnEl']")
        button.click()

        table = driver.find_element_by_xpath("(//table[contains(@class, 'x-grid-table')])[2]")
        tr_list = table.find_elements_by_xpath("./tbody/tr")[1:]
        for tr in tr_list:
            td_list = tr.find_elements_by_xpath("./td/div")
            for td in td_list:
                print(td.text)

        yield ToContainerPageRoutingRule.build_request_option(container_no_list=container_no_list, cookies=cookies)
