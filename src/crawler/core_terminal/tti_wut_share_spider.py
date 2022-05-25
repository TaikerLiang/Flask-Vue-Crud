import dataclasses
import time
from typing import List

import scrapy
from scrapy import Selector
from selenium.common.exceptions import NoAlertPresentException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from crawler.core.selenium import ChromeContentGetter
from crawler.core.table import BaseTable
from crawler.core_terminal.base import TERMINAL_RESULT_STATUS_ERROR
from crawler.core_terminal.base_spiders import BaseMultiTerminalSpider
from crawler.core_terminal.exceptions import TerminalInvalidContainerNoError
from crawler.core_terminal.items import DebugItem, ExportErrorData, TerminalItem
from crawler.core_terminal.request_helpers import RequestOption
from crawler.core_terminal.rules import BaseRoutingRule, RuleManager

MAX_PAGE_NUM = 20


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
            if isinstance(result, TerminalItem) or isinstance(result, ExportErrorData):
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
                dont_filter=True,
            )

        else:
            raise RuntimeError()


class MainRoutingRule(BaseRoutingRule):
    name = "MAIN"

    @classmethod
    def build_request_option(cls, container_no_list: List, company_info: CompanyInfo) -> RequestOption:
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url="https://eval.edi.hardcoretech.co/c/livez",
            meta={
                "container_no_list": container_no_list,
                "company_info": company_info,
            },
        )

    def handle(self, response):
        company_info = response.meta["company_info"]
        container_no_list = response.meta["container_no_list"]

        content_getter = ContentGetter(proxy_manager=None, is_headless=True)
        content_getter.login(company_info.email, company_info.password, company_info.url)

        while True:
            resp = None

            try:
                resp = content_getter.search(container_no_list[:MAX_PAGE_NUM], company_info.upper_short)
            except TerminalInvalidContainerNoError:  # all input container_no is invalid
                for container_no in container_no_list[:MAX_PAGE_NUM]:
                    yield ExportErrorData(
                        container_no=container_no,
                        detail="Data was not found",
                        status=TERMINAL_RESULT_STATUS_ERROR,
                    )
                return

            resp = Selector(text=resp)

            for item in self._handle_response(resp, container_no_list[:MAX_PAGE_NUM]):
                yield item

            if len(container_no_list) <= MAX_PAGE_NUM:
                content_getter.quit()
                break

            container_no_list = container_no_list[MAX_PAGE_NUM:]

    @classmethod
    def _handle_response(cls, response, container_no_list):
        containers = cls._extract_container_info(response, len(container_no_list))
        for container in containers:
            yield TerminalItem(
                **container,
            )
            container_no_list.remove(container["container_no"])

        for container_no in container_no_list:
            yield ExportErrorData(
                container_no=container_no,
                detail="Data was not found",
                status=TERMINAL_RESULT_STATUS_ERROR,
            )

    @staticmethod
    def _extract_container_info(response: Selector, numbers: int):
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
                "yard_location": table_locator.get_cell(left=i, top="Yard Location"),
                "ready_for_pick_up": table_locator.get_cell(left=i, top="Available for Pickup"),
                "available": table_locator.get_cell(left=i, top="Available for Pickup"),
                "appointment_date": table_locator.get_cell(left=i, top="Appt Time"),
                "carrier_release": table_locator.get_cell(left=i, top="Freight Status"),
                "holds": table_locator.get_cell(left=i, top="Hold Reason"),
                "last_free_day": table_locator.get_cell(left=i, top="Last Free Day"),
            }

            if container["container_no"]:
                res.append(container)

        return res


class ContentGetter(ChromeContentGetter):
    def login(self, username, password, url):
        self._driver.get(url)
        time.sleep(8)
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
        self._driver.switch_to.default_content()
        if short_name == "TTI":
            menu_btn = self._driver.find_element_by_xpath('//*[@id="nav"]/li[4]/a')
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

        # handle alert if there is any
        if self.is_alert_present():
            raise TerminalInvalidContainerNoError

        return self._driver.page_source

    def is_alert_present(self):
        try:
            self._driver.switch_to.alert.accept()
            return True
        except NoAlertPresentException:
            return False

    def quit(self):
        self._driver.quit()


class ContainerTableLocator(BaseTable):
    def parse(self, table: Selector, numbers: int = 1):
        titles_ths = table.css("th")
        title_list = []
        for title in titles_ths:
            title_res = (" ".join(title.css("::text").extract())).strip()
            title_list.append(title_res)

        trs = table.css("tr")
        index = 0
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
            self.add_left_header_set(index)
            index += 1
            for title_index, title in enumerate(title_list):
                self._td_map.setdefault(title, [])
                self._td_map[title].append(data_list[title_index])

    def get_cell(self, top=0, left=0) -> scrapy.Selector:
        if self.has_header(top, left):
            return self._td_map[top][left]
        else:
            return None
