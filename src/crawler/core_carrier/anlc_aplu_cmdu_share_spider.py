from typing import Optional, List, Dict
import re
import time
import dataclasses
import logging

import scrapy
from scrapy import Selector
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException
from urllib3.exceptions import ReadTimeoutError

from crawler.core.table import BaseTable, TableExtractor
from crawler.core_carrier.base import SHIPMENT_TYPE_MBL, SHIPMENT_TYPE_BOOKING
from crawler.core_carrier.exceptions import (
    CarrierResponseFormatError,
    SuspiciousOperationError,
    DriverMaxRetryError,
    ExportErrorData,
)
from crawler.core_carrier.items import (
    BaseCarrierItem,
    MblItem,
    LocationItem,
    ContainerItem,
    ContainerStatusItem,
    DebugItem,
)
from crawler.core_carrier.base_spiders import BaseMultiCarrierSpider
from crawler.core_carrier.request_helpers import RequestOption
from crawler.core.proxy import ProxyManager, HydraproxyProxyManager
from crawler.core_carrier.rules import RuleManager, BaseRoutingRule
from crawler.extractors.table_cell_extractors import BaseTableCellExtractor
from crawler.core.selenium import ChromeContentGetter
from crawler.core.defines import BaseContentGetter
from crawler.core_carrier.base import CARRIER_RESULT_STATUS_ERROR

STATUS_ONE_CONTAINER = "STATUS_ONE_CONTAINER"
STATUS_MULTI_CONTAINER = "STATUS_MULTI_CONTAINER"
STATUS_MBL_NOT_EXIST = "STATUS_MBL_NOT_EXIST"
STATUS_WEBSITE_SUSPEND = "STATUS_WEBSITE_SUSPEND"
MAX_RETRY_COUNT = 3


@dataclasses.dataclass
class Restart:
    search_nos: list
    task_ids: list
    reason: str = ""


class ContentGetter(ChromeContentGetter):
    def __init__(
        self, proxy_manager: Optional[ProxyManager] = None, is_headless: bool = False, load_image: bool = True
    ):
        super().__init__(proxy_manager=proxy_manager, is_headless=is_headless, load_image=load_image)

    def search(self, search_no: str):
        self._driver.get("https://www.apl.com/")
        WebDriverWait(self._driver, 30).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="wrapper"]/div/div[2]/div/div[1]/nav/ul/li[2]/a/span'))
        )
        time.sleep(2)
        self._driver.find_element_by_xpath('//*[@id="wrapper"]/div/div[2]/div/div[1]/nav/ul/li[2]/a/span').click()
        time.sleep(2)
        ref = self._driver.find_element_by_xpath('//*[@id="track-number"]')
        ref.send_keys(search_no)
        time.sleep(2)
        submit_btn = self._driver.find_element_by_xpath('//*[@id="searchTracking"]')
        submit_btn.click()
        time.sleep(20)

        return self._driver.page_source

    def handle_muti_container(self):
        page_contents = []
        WebDriverWait(self._driver, 30).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="multiresultssection"]/div/div/ul/li'))
        )
        cards = self._driver.find_elements_by_xpath('//*[@id="multiresultssection"]/div/div/ul/li')
        for card in cards:
            self._driver.execute_script("window.open('','_blank');")
            time.sleep(3)
            link = card.find_element_by_tag_name("a").get_attribute("href")
            self.switch_to_last_window()
            self._driver.get(link)
            time.sleep(30)
            self.scroll_to_bottom_of_page()
            time.sleep(2)
            page_contents.append(self._driver.page_source)
            self.close_current_window_and_jump_to_origin()

        return page_contents

    def close_current_window_and_jump_to_origin(self):
        self._driver.close()

        # jump back to origin window
        windows = self._driver.window_handles
        assert len(windows) == 1
        self._driver.switch_to.window(windows[0])


class AnlcApluCmduShareSpider(BaseMultiCarrierSpider):
    name = ""
    base_url = ""

    def __init__(self, *args, **kwargs):
        super(AnlcApluCmduShareSpider, self).__init__(*args, **kwargs)

        self.custom_settings.update({"CONCURRENT_REQUESTS": "1"})

        self._proxy_manager = HydraproxyProxyManager(session="cmdushare", logger=self.logger)
        self._content_getter = ContentGetter(proxy_manager=self._proxy_manager, is_headless=True, load_image=False)
        self._retry_count = 0

        bill_rules = [
            CargoTrackingRule(content_getter=self._content_getter),
            NextRoundRoutingRule(),
        ]

        booking_rules = [
            CargoTrackingRule(content_getter=self._content_getter),
            NextRoundRoutingRule(),
        ]

        if self.search_type == SHIPMENT_TYPE_MBL:
            self._rule_manager = RuleManager(rules=bill_rules)
        elif self.search_type == SHIPMENT_TYPE_BOOKING:
            self._rule_manager = RuleManager(rules=booking_rules)

    def start(self):
        self._proxy_manager.renew_proxy()
        option = CargoTrackingRule.build_request_option(search_nos=self.search_nos, task_ids=self.task_ids)
        proxy_option = self._proxy_manager.apply_proxy_to_request_option(option=option)
        yield self._build_request_by(option=proxy_option)

    def _prepare_start(self, search_nos: List, task_ids: List):
        self._content_getter.quit()
        self._proxy_manager.renew_proxy()
        self._content_getter = ContentGetter(proxy_manager=self._proxy_manager, is_headless=True, load_image=False)
        self._rule_manager.get_rule_by_name(CargoTrackingRule.name).assign_content_getter(
            content_getter=self._content_getter
        )
        option = CargoTrackingRule.build_request_option(search_nos=search_nos, task_ids=task_ids)
        proxy_option = self._proxy_manager.apply_proxy_to_request_option(option=option)
        return proxy_option

    def parse(self, response):
        yield DebugItem(info={"meta": dict(response.meta)})

        routing_rule = self._rule_manager.get_rule_by_response(response=response)
        save_name = routing_rule.get_save_name(response=response)
        self._saver.save(to=save_name, text=response.text)

        for result in routing_rule.handle(response=response):
            if isinstance(result, BaseCarrierItem):
                yield result
            elif isinstance(result, RequestOption):
                proxy_option = self._proxy_manager.apply_proxy_to_request_option(result)
                yield self._build_request_by(option=proxy_option)
            elif isinstance(result, Restart):
                self._retry_count += 1
                search_nos = result.search_nos
                task_ids = result.task_ids
                if self._retry_count > MAX_RETRY_COUNT:
                    raise DriverMaxRetryError()
                proxy_option = self._prepare_start(search_nos=search_nos, task_ids=task_ids)
                yield self._build_request_by(option=proxy_option)
            else:
                # raise RuntimeError()
                pass

    def _build_request_by(self, option: RequestOption):
        meta = {
            RuleManager.META_CARRIER_CORE_RULE_NAME: option.rule_name,
            **option.meta,
        }

        if option.method == RequestOption.METHOD_GET:
            return scrapy.Request(
                url=option.url,
                headers=option.headers,
                meta=meta,
                dont_filter=True,
            )
        elif option.method == RequestOption.METHOD_POST_FORM:
            return scrapy.FormRequest(
                url=option.url,
                headers=option.headers,
                formdata=option.form_data,
                meta=meta,
                dont_filter=True,
            )
        else:
            raise SuspiciousOperationError(msg=f"Unexpected request method: `{option.method}`")


class CargoTrackingRule(BaseRoutingRule):
    name = "CARGO_TRACKING"

    def __init__(self, content_getter: BaseContentGetter):
        self.content_getter = content_getter

    def assign_content_getter(self, content_getter: BaseContentGetter):
        self.content_getter = content_getter

    @classmethod
    def build_request_option(cls, search_nos: List, task_ids: List):
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=f"https://api.myip.com",
            meta={
                "search_nos": search_nos,
                "task_ids": task_ids,
            },
        )

    def get_save_name(self, response) -> str:
        return f"{self.name}.html"

    def handle(self, response):
        search_nos = response.meta["search_nos"]
        task_ids = response.meta["task_ids"]

        try:
            page_source = self.content_getter.search(search_nos[0])
            resp_selector = Selector(text=page_source)

            if not self._is_result_exist(response=resp_selector):
                yield ExportErrorData(
                    task_id=task_ids[0],
                    booking_no=search_nos[0],
                    status=CARRIER_RESULT_STATUS_ERROR,
                    detail="Data was not found",
                )
            else:
                container_list = self._extract_container_list(response=resp_selector)
                if len(container_list) > 0:
                    page_contents = self.content_getter.handle_muti_container()
                    for content in page_contents:
                        resp_selector = Selector(text=content)
                        for item in self.process_single_container_case(
                            response=resp_selector, search_no=search_nos[0], task_id=task_ids[0]
                        ):
                            yield item
                else:
                    for item in self.process_single_container_case(
                        response=resp_selector, search_no=search_nos[0], task_id=task_ids[0]
                    ):
                        yield item

            yield NextRoundRoutingRule.build_request_option(
                search_nos=search_nos,
                task_ids=task_ids,
            )

        except (TimeoutException, ReadTimeoutError, WebDriverException) as e:
            logging.error(str(e))
            yield Restart(reason="TimeoutException", search_nos=search_nos, task_ids=task_ids)

    def process_single_container_case(self, response: Selector, search_no: str, task_id: str):
        main_info = self._extract_basic_status(response=response)
        yield MblItem(
            task_id=task_id,
            pol=LocationItem(name=main_info["pol"]),
            pod=LocationItem(name=main_info["pod"]),
            eta=main_info["pod_eta"],
            ata=main_info["pod_ata"],
            container_quantity=main_info["container_quantity"],
        )

        container_no = main_info["container_no"]

        yield ContainerItem(
            task_id=task_id,
            container_key=container_no,
            container_no=container_no,
        )
        for container_status in self._extract_container_status(response=response):
            yield ContainerStatusItem(
                task_id=task_id,
                container_key=container_no,
                local_date_time=container_status["local_date_time"],
                description=container_status["description"],
                vessel=container_status["vessel"],
                voyage=container_status["voyage"],
                location=LocationItem(name=container_status["location"]),
                facility=container_status["facility"],
                est_or_actual="A",
            )

    @staticmethod
    def _is_result_exist(response: Selector):
        result_msg = response.css(
            "#shipmenttracking > section.tracking-details > div > div > div.left > span::text"
        ).get()
        if result_msg and result_msg.strip() == "No results found":
            return False
        return True

    @staticmethod
    def _extract_basic_status(response: Selector):
        container_no = response.css(
            "#trackingsearchsection > header > div > div > div > ul > li:nth-child(1) > strong::text"
        ).get()
        container_quantity = response.css(
            "#trackingsearchsection > header > div > div > div > ul > li.ico-container > strong::text"
        ).get()
        pol = response.css("#pol > div.timeline--item-description > span > strong::text").get()
        pod = response.css(
            "#trackingsearchsection > div > section > div > ul > li.timeline--item.arrival > div.timeline--item-description > span > strong::text"
        ).get()
        status = response.css(
            "#trackingsearchsection > div > section > div > div > div > div.status > span::text"
        ).get()
        arrive_time_list = response.css(
            "#trackingsearchsection > div > section > div > div > div > div.status > span > strong::text"
        ).getall()
        arrive_time = " ".join(arrive_time_list)
        pod_eta = None
        pod_ata = None

        if not status:
            pod_eta = None
        elif status.strip() == "ETA Berth at POD":
            pod_eta = arrive_time.strip()
        elif status.strip() == "Arrived at POD":
            pod_eta = None
            pod_ata = arrive_time.strip()
        elif status.strip() == "Remaining":
            pod_eta = None
        else:
            raise CarrierResponseFormatError(reason=f"Unknown status {status!r}")

        return {
            "container_no": container_no,
            "container_quantity": container_quantity,
            "pol": pol,
            "pod": pod,
            "pod_eta": pod_eta,
            "pod_ata": pod_ata,
        }

    @staticmethod
    def _extract_container_list(response: Selector) -> List:
        return response.css("#multiresultssection > div > div > ul > li").getall()

    @staticmethod
    def _extract_container_status(response) -> Dict:
        table_selector = response.css("#gridTrackingDetails")
        table_locator = ContainerStatusTableLocator()
        table_locator.parse(table=table_selector)
        table = TableExtractor(table_locator=table_locator)

        for index in table_locator.iter_left_header():
            yield {
                "local_date_time": table.extract_cell("Date", index).replace(",", ""),
                "description": table.extract_cell("Moves", index),
                "location": table.extract_cell("Location", index, LocationTdExtractor()),
                "vessel": table.extract_cell("Vessel", index),
                "voyage": table.extract_cell("Voyage", index),
                "facility": table.extract_cell("Location", index, FacilityTextExtractor()),
            }


class NextRoundRoutingRule(BaseRoutingRule):
    name = "NEXT_ROUND"

    @classmethod
    def build_request_option(cls, search_nos: List, task_ids: List) -> RequestOption:
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url="http://tracking.hardcoretech.co:18110",
            meta={
                "search_nos": search_nos,
                "task_ids": task_ids,
                "handle_httpstatus_list": [404],
            },
        )

    def handle(self, response):
        task_ids = response.meta["task_ids"]
        search_nos = response.meta["search_nos"]

        if len(search_nos) == 1 and len(task_ids) == 1:
            return

        task_ids = task_ids[1:]
        search_nos = search_nos[1:]

        yield CargoTrackingRule.build_request_option(search_nos=search_nos, task_ids=task_ids)


class ContainerStatusTableLocator(BaseTable):
    def parse(self, table: Selector):
        title_th_list = table.css("thead th")
        title_text_list = [title.strip() for title in title_th_list.css("::text").getall()]
        data_tr_list = table.css("tbody tr[class]")

        for index, tr in enumerate(data_tr_list):
            tds = tr.css("td")
            self._left_header_set.add(index)
            for title_index, (title, td) in enumerate(zip(title_text_list, tds)):
                self._td_map.setdefault(title, [])
                self._td_map[title].append(td)


class ActualIconTdExtractor(BaseTableCellExtractor):
    def extract(self, cell: Selector):
        td_i = cell.css("i").get()
        return td_i


class LocationTdExtractor(BaseTableCellExtractor):
    def extract(self, cell: Selector):
        td_i = cell.css("td::text").get().strip()
        return td_i


class FacilityTextExtractor(BaseTableCellExtractor):
    def extract(self, cell: Selector):
        TAG_RE = re.compile(r"<[^>]+>")
        i_text = cell.css("script#location__1::text").get(default="").strip()
        facility = TAG_RE.sub("", i_text)
        return facility
