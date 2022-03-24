import time
from pathlib import Path
from typing import List

import scrapy
from scrapy.selector import Selector
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from crawler.core.selenium import ChromeContentGetter
from crawler.core_carrier.base import CARRIER_RESULT_STATUS_ERROR
from crawler.core_carrier.base_spiders import BaseMultiCarrierSpider
from crawler.core_carrier.exceptions import (
    DriverMaxRetryError,
    SuspiciousOperationError,
)
from crawler.core_carrier.items import (
    BaseCarrierItem,
    ContainerItem,
    ContainerStatusItem,
    DebugItem,
    ExportErrorData,
    LocationItem,
    MblItem,
    VesselItem,
)
from crawler.core_carrier.request_helpers import RequestOption
from crawler.core_carrier.rules import BaseRoutingRule, RequestOptionQueue, RuleManager
from crawler.services.captcha_service import CaptchaSolverService

SITC_BASE_URL = "https://api.sitcline.com/sitcline"
SITC_SEARCH_URL = f"{SITC_BASE_URL}/query/cargoTrack"
MAX_RETRY_COUNT = 5


class CarrierSitcSpider(BaseMultiCarrierSpider):
    name = "carrier_sitc_multi"

    def __init__(self, *args, **kwargs):
        super(CarrierSitcSpider, self).__init__(*args, **kwargs)

        self.custom_settings.update({"CONCURRENT_REQUESTS": "1"})
        self._content_getter = ContentGetter(proxy_manager=None, is_headless=True)
        self._content_getter.connect()

        rules = [
            TracingRoutingRule(self._content_getter),
            ContainerStatusRoutingRule(self._content_getter),
            NextRoundRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)
        self._request_queue = RequestOptionQueue()

    def start(self):
        request_option = TracingRoutingRule.build_request_option(mbl_nos=self.mbl_nos, task_ids=self.task_ids)
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
            url="https://eval.edi.hardcoretech.co/c/livez",
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
        if self._is_mbl_no_invalid(mbl_page):
            yield ExportErrorData(
                mbl_no=current_mbl_no,
                task_id=current_task_id,
                status=CARRIER_RESULT_STATUS_ERROR,
                detail="Data was not found",
            )
            yield NextRoundRoutingRule.build_request_option(mbl_nos=mbl_nos, task_ids=task_ids)
            return

        basic_info = self._extract_basic_info(page=mbl_page)
        if basic_info:
            yield MblItem(
                mbl_no=basic_info["mbl_no"],
                task_id=current_task_id,
                pol=LocationItem(name=basic_info["pol_name"]),
                final_dest=LocationItem(name=basic_info["final_dest_name"]),
            )
        else:
            yield ExportErrorData(
                mbl_no=current_mbl_no, status=CARRIER_RESULT_STATUS_ERROR, detail="Data was not found"
            )
            yield NextRoundRoutingRule.build_request_option(mbl_nos=mbl_nos, task_ids=task_ids)
            return

        vessel_info_list = self._extract_vessel_info_list(page=mbl_page)
        for vessel in vessel_info_list:
            vessel_name = vessel["vessel"]
            yield VesselItem(
                task_id=current_task_id,
                vessel_key=vessel_name,
                vessel=vessel_name,
                voyage=vessel["voyage"],
                pol=LocationItem(name=vessel["pol_name"]),
                pod=LocationItem(name=vessel["pod_name"]),
                etd=vessel["etd"] or None,
                atd=vessel["atd"] or None,
                eta=vessel["eta"] or None,
                ata=vessel["ata"] or None,
            )

        container_info_list = self._extract_container_info_list(page=mbl_page)
        for container in container_info_list:
            container_no = container["container_no"]
            yield ContainerItem(
                task_id=current_task_id,
                container_key=container_no,
                container_no=container_no,
            )

            yield ContainerStatusRoutingRule.build_request_option(container_no=container_no, task_id=current_task_id)

        yield NextRoundRoutingRule.build_request_option(mbl_nos=mbl_nos, task_ids=task_ids)

    @staticmethod
    def _extract_basic_info(page):
        selector = Selector(text=page)
        thead = selector.xpath("//table[@class='el-table__header']//thead")[0]
        tbody = selector.xpath("//table[@class='el-table__body']//tbody")[0]

        headers = Extractor.extract_ths(thead)
        entries = Extractor.extract_trs(tbody)

        info = Extractor.extract_table(headers, entries)[0]
        return {
            "mbl_no": info["B/L No"],
            "pol_name": info["POL"],
            "final_dest_name": info["Final Destination"],
        }

    @staticmethod
    def _extract_vessel_info_list(page) -> List:
        selector = Selector(text=page)
        thead = selector.xpath("//table[@class='el-table__header']//thead")[1]
        tbody = selector.xpath("//table[@class='el-table__body']//tbody")[1]

        headers = Extractor.extract_ths(thead)
        entries = Extractor.extract_trs(tbody)

        info_list = []
        vessels = Extractor.extract_table(headers, entries)
        for vessel in vessels:
            info_list.append(
                {
                    "vessel": vessel["VesselName"],
                    "voyage": vessel["Voyage"],
                    "pol_name": vessel["POL"],
                    "pod_name": vessel["POD"],
                    "etd": vessel["ETD/ATD"],
                    "atd": vessel["ETD/ATD"],
                    "eta": vessel["ETA/ATA"],
                    "ata": vessel["ETA/ATA"],
                }
            )

        return info_list

    @staticmethod
    def _extract_container_info_list(page) -> List:
        selector = Selector(text=page)
        thead = selector.xpath("//table[@class='el-table__header']//thead")[2]
        tbody = selector.xpath("//table[@class='el-table__body']//tbody")[2]

        headers = Extractor.extract_ths(thead)
        entries = Extractor.extract_trs(tbody, ignore_1st_col=True)

        info_list = []
        containers = Extractor.extract_table(headers, entries)
        for container in containers:
            info_list.append({"container_no": container["Container No"]})

        return info_list

    @staticmethod
    def _is_mbl_no_invalid(page):
        selector = Selector(text=page)
        error_message = selector.css("span.el-table__empty-text::text").get()
        if not error_message:
            return

        error_message.strip()
        return error_message.startswith("暂无数据")


# -------------------------------------------------------------------------------


class ContainerStatusRoutingRule(BaseRoutingRule):
    name = "CONTAINER_STATUS"

    def __init__(self, content_getter):
        self._content_getter = content_getter

    @classmethod
    def build_request_option(cls, container_no: str, task_id: str) -> RequestOption:
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url="https://eval.edi.hardcoretech.co/c/livez",
            meta={"container_key": container_no, "task_id": task_id},
        )

    def get_save_name(self, response) -> str:
        container_key = response.meta["container_key"]
        return f"{self.name}_{container_key}.json"

    def handle(self, response):
        task_id = response.meta["task_id"]
        container_key = response.meta["container_key"]

        page = self._content_getter.get_container_status_page(container_key)
        container_status_list = self._extract_container_status_list(page=page)
        for container_status in container_status_list:
            yield ContainerStatusItem(
                task_id=task_id,
                container_key=container_key,
                description=container_status["description"],
                local_date_time=container_status["local_date_time"],
                location=LocationItem(name=container_status["location_name"]),
            )

    @staticmethod
    def _extract_container_status_list(page) -> List:
        selector = Selector(text=page)
        thead = selector.xpath("//table[@class='el-table__header']//thead")[-1]
        tbody = selector.xpath("//table[@class='el-table__body']//tbody")[-1]

        headers = Extractor.extract_ths(thead)
        entries = Extractor.extract_trs(tbody, ignore_1st_col=True)

        info_list = []
        status_list = Extractor.extract_table(headers, entries)
        for status in status_list:
            info_list.append(
                {
                    "local_date_time": status["Occurrence Time"],  # Occurence Time
                    "description": status["Current Status"],  # Current Status
                    "location_name": status["Local"],  # Local
                }
            )

        return info_list


# -------------------------------------------------------------------------------


class NextRoundRoutingRule(BaseRoutingRule):
    name = "ROUTING"

    @classmethod
    def build_request_option(cls, mbl_nos: List, task_ids: List) -> RequestOption:
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url="https://eval.edi.hardcoretech.co/c/livez",
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


class Extractor:
    @staticmethod
    def extract_table(headers: List, entries: List):
        _json = []
        for entry in entries:
            row = {}
            for i, data in enumerate(entry):
                row[headers[i]] = data

            _json.append(row)

        return _json

    @staticmethod
    def extract_ths(thead: scrapy.Selector):
        headers = thead.xpath(".//text()").getall()
        return [x.strip() for x in headers]

    @staticmethod
    def extract_trs(tbody: scrapy.Selector, ignore_1st_col: bool = False):
        entries = []
        trs = tbody.xpath(".//tr")

        for tr in trs:
            entry = tr.xpath(".//text()").getall()
            if ignore_1st_col:
                entry = entry[1:]

            entry = [x.strip() for x in entry]
            entries.append(entry)

        return entries


# -------------------------------------------------------------------------------


class ContentGetter(ChromeContentGetter):
    USERNAME = "GoFreight"
    PASSWORD = "hardcore@2021"
    CAPTCHA_NAME = "captcha.png"
    CAPTCHA_PATH = Path("carrier_sitc_multi.py").absolute().parents[0] / CAPTCHA_NAME
    MAX_CAPTCHA_RETRY = 3

    def __init__(self, proxy_manager, is_headless):
        super().__init__(proxy_manager=proxy_manager, is_headless=is_headless)
        self.retry_count = 0
        self.captcha_retry_count = 0

    def connect(self):
        self._driver.get(f"{SITC_BASE_URL}/wel")
        login_button_css = "a.login.click-able"
        time.sleep(60)

        try:
            WebDriverWait(self._driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, login_button_css)))
            self._driver.find_element(By.CSS_SELECTOR, login_button_css).click()
            self._login()

            # wait until login
            time.sleep(5)
            self._driver.get(SITC_SEARCH_URL)
            time.sleep(5)

        except TimeoutException:
            self.restart()

    def _login(self):
        login_dialog_css = "div.el-dialog__body"

        WebDriverWait(self._driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, login_dialog_css)))

        login_window = self._driver.find_element(By.CSS_SELECTOR, login_dialog_css)
        captcha_ele = login_window.find_element(By.XPATH, "//img[@class='login-code-img']")

        login_window.find_element(By.XPATH, "//input[@placeholder='请输入登陆用户名']").send_keys(self.USERNAME)
        login_window.find_element(By.XPATH, "//input[@placeholder='请输入密码']").send_keys(self.PASSWORD)

        dialog_wrapper = self._driver.find_element_by_css_selector("div.el-dialog__wrapper")
        while not self._is_captcha_solved(dialog_wrapper):
            login_window.find_element(By.XPATH, "//input[@placeholder='请输入验证码']").send_keys(
                self._solve_captcha(captcha_ele)
            )
            login_window.find_element(By.CSS_SELECTOR, "button.el-button.el-button--danger.el-button--medium").click()

    def _is_captcha_solved(self, dialog_wrapper):
        style = self._driver.execute_script("return arguments[0].getAttribute('style');", dialog_wrapper)
        return "display: None" in style

    def _solve_captcha(self, ele: WebElement):
        if self.captcha_retry_count > self.MAX_CAPTCHA_RETRY:
            raise DriverMaxRetryError()

        self.captcha_retry_count += 1
        ele.screenshot("captcha.png")

        return CaptchaSolverService().solve_image(file_path=self.CAPTCHA_PATH)

    def restart(self):
        if self.retry_count >= MAX_RETRY_COUNT:
            raise DriverMaxRetryError()

        self.retry_count += 1
        self._driver.close()
        self.connect()

    def get_mbl_page(self, mbl_no):
        WebDriverWait(self._driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@placeholder='请输入提单号']"))
        )
        mbl_input = self._driver.find_element(By.XPATH, "//input[@placeholder='请输入提单号']")
        mbl_input.send_keys(mbl_no)
        button = self._driver.find_element(
            By.CSS_SELECTOR, "button.el-button.search-form-btn.el-button--primary.el-button--small"
        )
        button.click()
        mbl_input.clear()

        WebDriverWait(self._driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "table.el-table__header"))
        )

        WebDriverWait(self._driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "table.el-table__body"))
        )

        # wait for the next mbl page to replace the previous
        time.sleep(5)

        return self._driver.page_source

    def get_container_status_page(self, container_no: str):
        span = self._driver.find_element(By.XPATH, f"//span[contains(text(), '{container_no}')]")
        button = span.find_element(By.XPATH, "./..")
        self._driver.execute_script("arguments[0].click();", button)  # display container status

        WebDriverWait(self._driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.el-dialog__body table.el-table__body"))
        )
        WebDriverWait(self._driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.el-dialog__headerbtn"))
        )

        close_button = self._driver.find_element(By.CSS_SELECTOR, "button.el-dialog__headerbtn")
        page_src = self._driver.page_source
        close_button.click()

        return page_src
