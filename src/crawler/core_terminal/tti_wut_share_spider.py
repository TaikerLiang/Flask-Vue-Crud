import time
import dataclasses
from typing import Dict, List

import scrapy
from scrapy import Selector
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from crawler.core_terminal.base_spiders import BaseMultiTerminalSpider
from crawler.core_terminal.items import DebugItem, TerminalItem, InvalidContainerNoItem
from crawler.core_terminal.request_helpers import RequestOption
from crawler.core_terminal.rules import RuleManager, BaseRoutingRule
from crawler.extractors.table_extractors import BaseTableLocator, HeaderMismatchError


@dataclasses.dataclass
class CompanyInfo:
    url: str
    upper_short: str
    email: str
    password: str


class TtiWutShareSpider(BaseMultiTerminalSpider):
    name = ""
    company_info = CompanyInfo(
        url="",
        upper_short="",
        email="",
        password="",
    )

    def __init__(self, *args, **kwargs):
        super(TtiWutShareSpider, self).__init__(*args, **kwargs)

        rules = [
            MainRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)

    def start(self):
        unique_container_nos = list(self.cno_tid_map.keys())
        option = MainRoutingRule.build_request_option(
            container_no_list=unique_container_nos, company_info=self.company_info
        )
        yield self._build_request_by(option=option)

    def parse(self, response, **kwargs):
        yield DebugItem(info={"meta": dict(response.meta)})

        routing_rule = self._rule_manager.get_rule_by_response(response=response)

        save_name = routing_rule.get_save_name(response=response)
        self._saver.save(to=save_name, text=response.text)

        for result in routing_rule.handle(response=response):
            if isinstance(result, TerminalItem) or isinstance(result, InvalidContainerNoItem):
                c_no = result["container_no"]
                t_ids = self.cno_tid_map[c_no]
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

        if option.method == RequestOption.METHOD_POST_FORM:
            return scrapy.FormRequest(
                url=option.url,
                formdata=option.form_data,
                meta=meta,
            )

        elif option.method == RequestOption.METHOD_GET:
            return scrapy.Request(
                url=option.url,
                meta=meta,
            )

        else:
            raise RuntimeError()


class MainRoutingRule(BaseRoutingRule):
    name = "MAIN"

    @classmethod
    def build_request_option(cls, container_no_list: List, company_info: CompanyInfo) -> RequestOption:
        url = "https://www.google.com"
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=url,
            meta={
                "container_no_list": container_no_list,
                "company_info": company_info,
            },
        )

    def handle(self, response):
        company_info = response.meta["company_info"]
        container_no_list = response.meta["container_no_list"]

        content_getter = ContentGetter()
        content_getter.login(company_info.email, company_info.password, company_info.url)
        resp = self._build_container_response(content_getter, container_no_list, company_info.upper_short)

        containers = content_getter.get_container_info(Selector(text=resp), len(container_no_list))
        content_getter.quit()

        for container in containers:
            yield TerminalItem(
                **container,
            )

    @staticmethod
    def _build_container_response(content_getter, container_no_list: List, short_name: str):
        return content_getter.search(container_no_list, short_name)


class ContentGetter:
    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-notifications")
        options.add_argument("--headless")
        options.add_argument("--enable-javascript")
        options.add_argument("--disable-gpu")
        options.add_argument(
            f"user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 11_1_0) AppleWebKit/537.36 (KHTML, like Gecko) "
            f"Chrome/88.0.4324.96 Safari/537.36"
        )
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        self._driver = webdriver.Chrome(options=options)

    def login(self, username, password, url):
        self._driver.get(url)
        time.sleep(5)
        username_input = self._driver.find_element_by_xpath('//*[@id="pUsrId"]')
        username_input.send_keys(username)
        time.sleep(2)
        password_input = self._driver.find_element_by_xpath('//*[@id="pUsrPwd"]')
        password_input.send_keys(password)
        time.sleep(2)
        login_btn = self._driver.find_element_by_xpath(
            '//*[@id="form"]/table/tbody/tr/td[1]/table/tbody/tr[3]/td/table[1]/tbody/tr[2]/td/table/tbody/tr[1]/td[3]/img'
        )
        login_btn.click()
        time.sleep(8)

    def search(self, container_no_list: List, short_name: str):
        if short_name == "TTI":
            menu_btn = self._driver.find_element_by_xpath('//*[@id="nav"]/li[3]/a')
        else:
            menu_btn = self._driver.find_element_by_xpath('//*[@id="nav"]/li[1]/a')

        menu_btn.click()
        time.sleep(10)

        # iframe = self._driver.find_element_by_xpath('//*[@id="businessView"]')
        WebDriverWait(self._driver, 30).until(EC.frame_to_be_available_and_switch_to_it((By.ID, "businessView")))

        container_text_area = self._driver.find_element_by_xpath('//*[@id="cntrNos"]')
        container_text_area.send_keys("\n".join(container_no_list))
        time.sleep(3)

        search_btn = self._driver.find_element_by_xpath(
            '//*[@id="form"]/table/tbody/tr/td/table/tbody/tr/td/table[2]/tbody/tr/td/table[1]/tbody/tr/td[1]/table[3]/tbody/tr/td/table/tbody/tr/td[1]/table/tbody/tr/td[2]/a'
        )
        search_btn.click()
        time.sleep(8)

        return self._driver.page_source

    def get_container_info(self, response: Selector, numbers: int):
        table = response.xpath('//*[@id="gview_grid1"]')
        table_locator = ContainerTableLocator()
        table_locator.parse(table=table, numbers=numbers)

        res = []
        for i in range(numbers):
            container = {
                "container_no": table_locator.get_cell(left=i, top="Container No"),
                "container_spec": table_locator.get_cell(left=i, top="Container Type/Length/Height"),
                "customs_release": table_locator.get_cell(left=i, top="Customs Status"),
                "cy_location": table_locator.get_cell(left=i, top="Yard Location"),
                "ready_for_pick_up": table_locator.get_cell(left=i, top="Available for Pickup"),
                "appointment_date": table_locator.get_cell(left=i, top="Appt Time"),
                "carrier_release": table_locator.get_cell(left=i, top="Freight Status"),
                "holds": table_locator.get_cell(left=i, top="Hold Reason"),
                "last_free_day": table_locator.get_cell(left=i, top="Last Free Day"),
            }

            if container["container_no"]:
                res.append(container)

        return res

    def quit(self):
        self._driver.quit()


class ContainerTableLocator(BaseTableLocator):
    def __init__(self):
        self._td_map = []

    def parse(self, table: Selector, numbers: int = 1):
        titles_ths = table.css("th")
        title_list = []
        for title in titles_ths:
            title_res = (" ".join(title.css("::text").extract())).strip()
            title_list.append(title_res)

        trs = table.css("tr")
        for tr in trs:
            data_tds = tr.css("td")
            data_list = []
            is_append = False
            for data in data_tds:
                data_res = (" ".join(data.css("::text").extract())).strip()
                if data_res:
                    is_append = True
                data_list.append(data_res)

            if not is_append:
                continue

            row = {}
            for title_index, title in enumerate(title_list):
                row[title] = data_list[title_index]

            self._td_map.append(row)

    def has_header(self, top=None, left=None) -> bool:
        return (top in self._td_map) and (left is None)

    def get_cell(self, top, left=0) -> scrapy.Selector:
        try:
            return self._td_map[left][top]
        except (KeyError, IndexError) as err:
            return None
