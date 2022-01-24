import time
from typing import List
from crawler.core.table import BaseTable

from scrapy import Request, FormRequest, Selector
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from crawler.core.table import HeaderMismatchError
from crawler.core.selenium import ChromeContentGetter
from crawler.core_terminal.base_spiders import BaseMultiTerminalSpider
from crawler.core_terminal.exceptions import LoadWebsiteTimeOutFatal
from crawler.core_terminal.items import DebugItem, TerminalItem, InvalidContainerNoItem
from crawler.core_terminal.rules import RuleManager, BaseRoutingRule, RequestOption
from crawler.extractors.selector_finder import BaseMatchRule, find_selector_from


MAX_PAGE_NUM = 3


class MaherContentGetter(ChromeContentGetter):
    USERNAME = "hard202006010"
    PASSWORD = "hardc0re"

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

    def login(self):
        self._driver.get("https://apps.maherterminals.com/csp/loginAction.do?method=login")

        try:
            WebDriverWait(self._driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='userBean.username']"))
            )
        except TimeoutException:
            raise LoadWebsiteTimeOutFatal()

        username_input = self._driver.find_element_by_css_selector("input[name='userBean.username']")
        password_input = self._driver.find_element_by_css_selector("input[name='userBean.password']")

        username_input.send_keys(self.USERNAME)
        password_input.send_keys(self.PASSWORD)

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

    def __init__(self, *args, **kwargs):
        super(TerminalMaherMultiSpider, self).__init__(*args, **kwargs)

        rules = [
            SearchRoutingRule(),
            NextRoundRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)
        self._max_retry_times = 3

    def start(self):
        unique_container_nos = list(self.cno_tid_map.keys())
        option = SearchRoutingRule.build_request_option(container_no_list=unique_container_nos)
        yield self._build_request_by(option=option)

    def parse(self, response):
        yield DebugItem(info={"meta": dict(response.meta)})

        routing_rule = self._rule_manager.get_rule_by_response(response=response)

        save_name = routing_rule.get_save_name(response=response)
        self._saver.save(to=save_name, text=response.text)

        try:
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
        except HeaderMismatchError as e:
            self._max_retry_times -= 1

            # retry searching
            if self._max_retry_times >= 0:
                unique_container_nos = list(self.cno_tid_map.keys())
                option = SearchRoutingRule.build_request_option(container_no_list=unique_container_nos)
                yield self._build_request_by(option=option)
            else:
                raise HeaderMismatchError("Already consumed all retry times")

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
    def build_request_option(cls, container_no_list: List[str]) -> RequestOption:
        url = "https://www.google.com"

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=url,
            meta={"container_no_list": container_no_list},
        )

    def get_save_name(self, response) -> str:
        return f"{self.name}.html"

    def handle(self, response):
        container_no_list = response.meta["container_no_list"]

        content_getter = MaherContentGetter(proxy_manager=None, is_headless=True)
        content_getter.login()
        response_text = content_getter.search(container_no_list[:MAX_PAGE_NUM])
        time.sleep(3)
        response = Selector(text=response_text)

        for item in self._handle_response(response, container_no_list[:MAX_PAGE_NUM]):
            yield item

        yield NextRoundRoutingRule.build_request_option(container_no_list=container_no_list)

    @classmethod
    def _handle_response(cls, response, container_no_list):
        container_info_list = cls.extract_container_info(response=response, container_no_list=container_no_list)
        for container_info in container_info_list:
            yield TerminalItem(**container_info)

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


class NextRoundRoutingRule(BaseRoutingRule):
    name = "NEXT_ROUND"

    @classmethod
    def build_request_option(cls, container_no_list: List) -> RequestOption:
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url="https://api.myip.com/",
            meta={
                "container_no_list": container_no_list,
            },
        )

    def handle(self, response):
        container_no_list = response.meta["container_no_list"]

        if len(container_no_list) <= MAX_PAGE_NUM:
            return

        container_no_list = container_no_list[MAX_PAGE_NUM:]

        yield SearchRoutingRule.build_request_option(container_no_list=container_no_list)


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


class MaherLeftHeadTableLocator(BaseTable):
    def parse(self, table: Selector, numbers: int = 1):
        titles = self._get_titles(table)
        trs = table.css("tbody tr")

        for index, tr in enumerate(trs):
            data_tds = tr.css("td a::text").getall() + tr.css("td::text").getall()
            data_tds = [v.strip() for v in data_tds]
            if len(data_tds) > len(titles):
                data_tds = data_tds[:1] + data_tds[3:]
            elif len(data_tds) == 2:
                data_tds = data_tds + [""] * 9
            else:
                continue

            self._left_header_set.add(index)

            for title, td in zip(titles, data_tds):
                self._td_map.setdefault(title, [])
                self._td_map[title].append(td)

    def _get_titles(self, table: Selector):
        titles = table.css("th::text").getall()
        return [title.strip() for title in titles]