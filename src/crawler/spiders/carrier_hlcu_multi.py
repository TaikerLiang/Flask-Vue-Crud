from typing import Dict, List

import scrapy
from scrapy.selector import Selector
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException

from crawler.core.base import DUMMY_URL_DICT
from crawler.core_carrier.base import CARRIER_RESULT_STATUS_ERROR
from crawler.core_carrier.base_spiders import BaseMultiCarrierSpider
from crawler.core_carrier.exceptions import (
    CarrierResponseFormatError,
    SuspiciousOperationError,
    LoadWebsiteTimeOutError,
)
from crawler.core_carrier.items import (
    BaseCarrierItem,
    ExportErrorData,
    LocationItem,
    ContainerItem,
    ContainerStatusItem,
    DebugItem,
)
from crawler.core_carrier.request_helpers import RequestOption
from crawler.core_carrier.rules import RuleManager, BaseRoutingRule, RequestOptionQueue
from crawler.core.selenium import ChromeContentGetter
from crawler.core.table import TableExtractor, BaseTable
from crawler.extractors.table_cell_extractors import BaseTableCellExtractor, FirstTextTdExtractor


BASE_URL = "https://www.hapag-lloyd.com/en"
SEARCH_URL = f"{BASE_URL}/online-business/track/track-by-booking-solution.html"

MAX_RETRY_COUNT = 1


class CarrierHlcuSpider(BaseMultiCarrierSpider):
    name = "carrier_hlcu_multi"

    def __init__(self, *args, **kwargs):
        super(CarrierHlcuSpider, self).__init__(*args, **kwargs)

        self.custom_settings.update({"CONCURRENT_REQUESTS": "1"})

        self._content_getter = ContentGetter()
        self._content_getter.connect()

        rules = [
            TracingRoutingRule(self._content_getter),
            NextRoundRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)
        self._request_queue = RequestOptionQueue()

    def start(self):
        request_option = TracingRoutingRule.build_request_option(mbl_nos=self.search_nos, task_ids=self.task_ids)
        yield self._build_request_by(option=request_option)

    def parse(self, response):
        yield DebugItem(info={"meta": dict(response.meta)})

        routing_rule = self._rule_manager.get_rule_by_response(response=response)

        save_name = routing_rule.get_save_name(response=response)
        self._saver.save(to=save_name, text=response.text)

        for result in routing_rule.handle(response=response):
            if isinstance(result, BaseCarrierItem):
                yield result
            elif isinstance(result, RequestOption):
                self._request_queue.add_request(result)
            else:
                raise RuntimeError()

        if not self._request_queue.is_empty():
            request_option = self._request_queue.get_next_request()
            yield self._build_request_by(option=request_option)

    def _build_request_by(self, option: RequestOption):
        meta = {
            RuleManager.META_CARRIER_CORE_RULE_NAME: option.rule_name,
            **option.meta,
        }

        if option.method == RequestOption.METHOD_GET:
            return scrapy.Request(
                url=option.url,
                cookies=option.cookies,
                meta=meta,
                dont_filter=True,
            )
        elif option.method == RequestOption.METHOD_POST_FORM:
            return scrapy.FormRequest(
                url=option.url,
                cookies=option.cookies,
                formdata=option.form_data,
                meta=meta,
                dont_filter=True,
            )
        else:
            raise SuspiciousOperationError(msg=f"Unexpected request method: `{option.method}`")


# -------------------------------------------------------------------------------


class TracingRoutingRule(BaseRoutingRule):
    name = "TRACING"

    def __init__(self, content_getter):
        self._content_getter = content_getter

    @classmethod
    def build_request_option(cls, mbl_nos: List, task_ids: List) -> RequestOption:
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=DUMMY_URL_DICT["google"],
            meta={"mbl_nos": mbl_nos, "task_ids": task_ids},
        )

    def get_save_name(self, response):
        return f"{self.name}.html"

    def handle(self, response):
        mbl_nos = response.meta["mbl_nos"]
        task_ids = response.meta["task_ids"]
        current_mbl_no = mbl_nos[0]
        current_task_id = task_ids[0]

        mbl_page = self._content_getter.get_mbl_page(mbl_no=current_mbl_no)
        selector = Selector(text=mbl_page)

        if self._is_mbl_no_invalid(selector):
            yield ExportErrorData(
                mbl_no=current_mbl_no,
                task_id=current_task_id,
                status=CARRIER_RESULT_STATUS_ERROR,
                detail="Data was not found",
            )
            yield NextRoundRoutingRule.build_request_option(mbl_nos=mbl_nos, task_ids=task_ids)
            return

        container_nos = []
        if self._is_container_nos_exist(selector):
            container_nos = self._extract_container_nos(response=selector)

        for index, container_no in enumerate(container_nos):
            yield ContainerItem(
                task_id=current_task_id,
                container_no=container_no,
                container_key=container_no,
            )

            container_page = self._content_getter.get_container_page(index=index)
            for status_item in self._handle_container(
                page=container_page, container_no=container_no, task_id=current_task_id
            ):
                yield status_item

        yield NextRoundRoutingRule.build_request_option(mbl_nos=mbl_nos, task_ids=task_ids)

    def _handle_container(self, page, container_no, task_id):
        selector = Selector(text=page)
        container_statuses = self._extract_container_statuses(response=selector)
        for container_status in container_statuses:
            yield ContainerStatusItem(
                task_id=task_id,
                container_key=container_no,
                description=container_status["description"],
                local_date_time=container_status["timestamp"],
                location=LocationItem(name=container_status["place"]),
                transport=container_status["transport"],
                voyage=container_status["voyage"],
                est_or_actual=container_status["est_or_actual"],
            )

    def _is_mbl_no_invalid(self, response):
        error_message = response.css('span[id="tracing_by_booking_f:hl15"]::text').get()
        if not error_message:
            return

        error_message.strip()
        return error_message.startswith("DOCUMENT does not exist.")

    def _is_container_nos_exist(self, response):
        table_selector = response.css("table[id='tracing_by_booking_f:hl27']")
        if table_selector:
            return True
        else:
            return False

    def _extract_container_nos(self, response):
        table_selector = response.css("table[id='tracing_by_booking_f:hl27']")

        table_locator = ContainerInfoTableLocator()
        table_locator.parse(table=table_selector)
        table = TableExtractor(table_locator=table_locator)
        span_extractor = FirstTextTdExtractor("span::text")

        container_list = []
        for left in table_locator.iter_left_header():
            container_no_text = table.extract_cell(top="Container No.", left=left, extractor=span_extractor)
            company, no = container_no_text.split()
            container_list.append(company + no)

        return container_list

    def _extract_container_statuses(self, response):
        table_selector = response.css("table[id='tracing_by_booking_f:hl66']")
        if not table_selector:
            CarrierResponseFormatError(reason="Can not find container_status table !!!")

        table_locator = ContainerStatusTableLocator()
        table_locator.parse(table=table_selector)
        table = TableExtractor(table_locator=table_locator)
        span_extractor = FirstTextTdExtractor(css_query="span::text")

        container_statuses = []
        for left in table_locator.iter_left_header():
            date = table.extract_cell(top="Date", left=left, extractor=span_extractor)
            time = table.extract_cell(top="Time", left=left, extractor=span_extractor) or "00:00"

            if date:
                timestamp = f"{date} {time}"
            else:
                timestamp = None

            class_name = table_locator.get_row_class(left=left)

            transport = table.extract_cell(top="Transport", left=left, extractor=span_extractor)
            status = table.extract_cell(top="Status", left=left, extractor=span_extractor)
            description = f"{status} ({transport})"

            container_statuses.append(
                {
                    "description": description,
                    "place": table.extract_cell(top="Place of Activity", left=left, extractor=span_extractor),
                    "timestamp": timestamp,
                    "transport": transport,
                    "voyage": table.extract_cell(top="Voyage No.", left=left, extractor=span_extractor) or None,
                    "est_or_actual": self._get_status_from(class_name),
                }
            )

        return container_statuses

    def _get_status_from(self, class_name):
        if class_name == "strong":
            return "A"
        elif not class_name:
            return "E"
        else:
            raise CarrierResponseFormatError(reason=f"Unknown status: `{class_name}`")


# -------------------------------------------------------------------------------


class NextRoundRoutingRule(BaseRoutingRule):
    name = "ROUTING"

    @classmethod
    def build_request_option(cls, mbl_nos: List, task_ids: List) -> RequestOption:
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=DUMMY_URL_DICT["google"],
            meta={"mbl_nos": mbl_nos, "task_ids": task_ids},
        )

    def handle(self, response):
        task_ids = response.meta["task_ids"]
        mbl_nos = response.meta["mbl_nos"]

        if len(mbl_nos) == 1 and len(task_ids) == 1:
            return

        task_ids = task_ids[1:]
        mbl_nos = mbl_nos[1:]

        yield TracingRoutingRule.build_request_option(mbl_nos=mbl_nos, task_ids=task_ids)


# -------------------------------------------------------------------------------


class ContainerInfoTableLocator(BaseTable):
    """
    +---------+---------+-----+---------+ <thead>
    | Title 1 | Title 2 | ... | Title N |     <th>
    +---------+---------+-----+---------+ </thead>
    +---------+---------+-----+---------+ <tbody>
    | Data    |         |     |         | <tr><td>
    +---------+---------+-----+---------+
    | Data    |         |     |         | <tr><td>
    +---------+---------+-----+---------+
    | ...     |         |     |         | <tr><td>
    +---------+---------+-----+---------+
    | Data    |         |     |         | <tr><td>
    +---------+---------+-----+---------+ </tbody>
    """

    def parse(self, table: scrapy.Selector):
        top_header_list = []

        for th in table.css("thead th"):
            raw_top_header = th.css("::text").get()
            top_header = raw_top_header.strip() if isinstance(raw_top_header, str) else ""
            top_header_list.append(top_header)
            self._td_map[top_header] = []

        data_tr_list = table.css("tbody tr")
        for index, tr in enumerate(data_tr_list):
            self._left_header_set.add(index)
            for top, td in zip(top_header_list, tr.css("td")):
                self._td_map[top].append(td)


class ContainerStatusTableLocator(BaseTable):
    def __init__(self):
        super().__init__()
        self._tr_classes = []

    def parse(self, table: scrapy.Selector):
        title_list = []
        tr_classes = []

        th_list = table.css("thead th")
        for th in th_list:
            title = th.css("span::text").get().strip()
            title_list.append(title)
            self._td_map[title] = []

        data_tr_list = table.css("tbody tr")
        for index, data_tr in enumerate(data_tr_list):
            self._left_header_set.add(index)
            tr_class_set = set()
            data_td_list = data_tr.css("td")
            for title, data_td in zip(title_list, data_td_list):
                data_td_class = data_td.css("td::attr(class)").get()
                tr_class_set.add(data_td_class)

                self._td_map[title].append(data_td)

            tr_classes.append(list(tr_class_set)[0])

        self._tr_classes = tr_classes

    def get_row_class(self, left):
        return self._tr_classes[left]


# -------------------------------------------------------------------------------


class ContentGetter(ChromeContentGetter):
    def __init__(self):
        super().__init__()
        self.retry_count = 0

    def connect(self):
        self._driver.get(SEARCH_URL)

        try:
            WebDriverWait(self._driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "button.save-preference-btn-handler.onetrust-close-btn-handler")
                )
            )
            button = self._driver.find_element(
                By.CSS_SELECTOR, "button.save-preference-btn-handler.onetrust-close-btn-handler"
            )
            button.click()
        except TimeoutException:
            self.restart()

    def restart(self):
        if self.retry_count >= MAX_RETRY_COUNT:
            raise LoadWebsiteTimeOutError(url=self._driver.current_url)

        self.retry_count += 1
        self._driver.close()
        self.connect()

    def get_mbl_page(self, mbl_no):
        self._driver.get(f"{SEARCH_URL}?blno={mbl_no}")
        return self._driver.page_source

    def get_container_page(self, index):
        self._driver.find_elements(By.CSS_SELECTOR, "div.hl-radio")[index].click()
        self._driver.find_elements(By.CSS_SELECTOR, "button[value='Details']")[0].click()
        page_source = self._driver.page_source
        self._driver.back()
        return page_source
