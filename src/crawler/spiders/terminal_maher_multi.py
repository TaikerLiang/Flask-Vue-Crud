import json
import time
from typing import List

from scrapy import Request, FormRequest, Selector
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from crawler.core.selenium import ChromeContentGetter
from crawler.core_terminal.base_spiders import BaseMultiTerminalSpider
from crawler.core_terminal.exceptions import LoadWebsiteTimeOutFatal
from crawler.core_terminal.items import DebugItem, TerminalItem, InvalidContainerNoItem
from crawler.core_terminal.rules import RuleManager, BaseRoutingRule, RequestOption
from crawler.extractors.selector_finder import BaseMatchRule, find_selector_from
from crawler.extractors.table_extractors import BaseTableLocator, HeaderMismatchError


class MaherContentGetter(ChromeContentGetter):
    def search(self, container_no_list: List):
        container_inquiry_text_area = self._driver.find_element_by_css_selector("textarea[name='equipment']")
        container_inquiry_text_area.clear()

        if len(container_no_list) == 1:
            container_no_list = container_no_list + container_no_list

        container_inquiry_text_area.send_keys("\n".join(container_no_list))

        search_btn = self._driver.find_element_by_css_selector("input[onclick='Search();']")
        search_btn.click()
        time.sleep(20)

        return self._driver.page_source

    def detail_search(self, container_no):
        self._driver.get(
            f"https://apps.maherterminals.com/csp/importContainerAction.do?container={container_no}&index=0&method=detail"
        )
        time.sleep(5)

        return self._driver.page_source

    def login(self, username, password):
        self._driver.get("https://apps.maherterminals.com/csp/loginAction.do?method=login")

        try:
            WebDriverWait(self._driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='userBean.username']"))
            )
        except TimeoutException:
            raise LoadWebsiteTimeOutFatal()

        username_input = self._driver.find_element_by_css_selector("input[name='userBean.username']")
        password_input = self._driver.find_element_by_css_selector("input[name='userBean.password']")

        username_input.send_keys(username)
        password_input.send_keys(password)

        login_btn = self._driver.find_element_by_css_selector("input[name='cancelButton']")
        login_btn.click()
        time.sleep(5)

        self._driver.get(
            "https://apps.maherterminals.com/csp/importContainerAction.do?method=initial&pageTitle=Import%20Container%20Status%20Inquiry"
        )
        time.sleep(5)


class TerminalMaherMultiSpider(BaseMultiTerminalSpider):
    firms_code = "E416"
    name = "terminal_maher_multi"
    USERNAME = "hard202006010"
    PASSWORD = "hardc0re"

    def __init__(self, *args, **kwargs):
        super(TerminalMaherMultiSpider, self).__init__(*args, **kwargs)

        rules = [
            SearchRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)

    def start(self):
        unique_container_nos = list(self.cno_tid_map.keys())
        option = SearchRoutingRule.build_request_option(
            container_no_list=unique_container_nos,
            username=self.USERNAME,
            password=self.PASSWORD,
        )
        yield self._build_request_by(option=option)

    def parse(self, response):
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
                method="POST",
            )
        else:
            raise ValueError(f"Invalid option.method [{option.method}]")


# -------------------------------------------------------------------------------


class SearchRoutingRule(BaseRoutingRule):
    name = "SEARCH"

    @classmethod
    def build_request_option(cls, container_no_list: List[str], username: str, password: str) -> RequestOption:
        url = "https://www.google.com"

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=url,
            meta={
                "container_no_list": container_no_list,
                "username": username,
                "password": password,
            },
        )

    def get_save_name(self, response) -> str:
        return f"{self.name}.html"

    def handle(self, response):
        container_no_list = response.meta["container_no_list"]
        username = response.meta["username"]
        password = response.meta["password"]

        content_getter = MaherContentGetter()
        content_getter.login(username=username, password=password)
        response_text = self._build_container_response(content_getter, container_no_list)

        time.sleep(3)
        response = Selector(text=response_text)
        container_info_list = self.extract_container_info(response=response, container_no_list=container_no_list)

        for container_info in container_info_list:
            ct_no = container_info["container_no"]
            # detail_page_resp = content_getter.detail_search(ct_no)
            # gate_out_date = detail_page_resp.xpath('/html/body/table/tbody/tr/td/div[3]/table/tbody/tr/td/table[4]/tbody/tr[4]/td/table/tbody/tr/td/table/tbody/tr[29]/td[2]/text()').get()
            # print(ct_no, detail_page_resp, gate_out_date)
            yield TerminalItem(**container_info)

    @staticmethod
    def _build_container_response(content_getter, container_no_list: List):
        return content_getter.search(container_no_list)

    @staticmethod
    def _is_container_no_invalid(response: Selector) -> bool:
        tables = response.css("table")
        rule = SpecificClassTdContainTextMatchRule(td_class="clsBlackBold", text="Not On File")
        return bool(find_selector_from(selectors=tables, rule=rule))

    @staticmethod
    def extract_container_info(response: Selector, container_no_list: List):
        table = response.xpath('//*[@id="sortTable"]')

        table_locator = MaherLeftHeadTableLocator()
        table_locator.parse(table=table, numbers=len(container_no_list))

        res = []
        for i in range(len(set(container_no_list))):
            res.append(
                {
                    "container_no": table_locator.get_cell(left=i, top="Container"),
                    "container_spec": table_locator.get_cell(left=i, top="LHT"),
                    "available": table_locator.get_cell(left=i, top="Available"),
                    "customs_release": table_locator.get_cell(left=i, top="Customs Released"),
                    "discharge_date": table_locator.get_cell(left=i, top="Date Discharged"),
                    "last_free_day": table_locator.get_cell(left=i, top="Last Free Date"),
                    "carrier_release": table_locator.get_cell(left=i, top="Freight Released"),
                }
            )

        return res


# -------------------------------------------------------------------------------


class SpecificClassTdContainTextMatchRule(BaseMatchRule):
    def __init__(self, td_class: str, text: str):
        self._td_class = td_class
        self._text = text

    def check(self, selector: Selector) -> bool:
        sub_headings = selector.xpath(f'./tbody/tr/td[@class="{self._td_class}"]') or selector.xpath(
            f'./tr/td[@class="{self._td_class}"]'
        )

        for sub_heading in sub_headings:
            sub_heading_text = sub_heading.css("::text").get().strip()
            if self._text in sub_heading_text:
                return True

        return False


class MaherLeftHeadTableLocator(BaseTableLocator):
    def __init__(self):
        self._td_map = []

    def parse(self, table: Selector, numbers: int = 1):
        titles = self._get_titles(table)
        trs = table.css("tbody tr")

        for tr in trs:
            data_tds = tr.css("td a::text").getall() + tr.css("td::text").getall()
            data_tds = [v.strip() for v in data_tds]
            if len(data_tds) > len(titles):
                data_tds = data_tds[:1] + data_tds[3:]
            elif len(data_tds) == 2:
                data_tds = data_tds + [""] * 9
            else:
                continue

            row = {}
            for title_index, title in enumerate(titles):
                row[title] = data_tds[title_index]
            self._td_map.append(row)

    def _get_titles(self, table: Selector):
        titles = table.css("th::text").getall()
        return [title.strip() for title in titles]

    def get_cell(self, left, top=None) -> Selector:
        try:
            return self._td_map[left][top]
        except (KeyError, IndexError) as err:
            raise HeaderMismatchError(repr(err))

    def has_header(self, top=None, left=None) -> bool:
        assert top is None
        return bool(self._td_map.get(left))
