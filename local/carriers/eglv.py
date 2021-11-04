import dataclasses
import asyncio
import logging

from scrapy import Request
from scrapy.http import TextResponse
from pyppeteer.errors import TimeoutError, ElementHandleError
from pyppeteer_stealth import stealth

from local.core import BaseLocalCrawler
from local.proxy import HydraproxyProxyManager, ProxyManager
from local.exceptions import DataNotFoundError
from crawler.core_carrier.request_helpers import RequestOption
from crawler.core_carrier.items import BaseCarrierItem
from src.crawler.core_carrier.base import SHIPMENT_TYPE_MBL, SHIPMENT_TYPE_BOOKING
from src.crawler.core_carrier.exceptions import LoadWebsiteTimeOutError, AntiCaptchaError
from src.crawler.core.pyppeteer import PyppeteerContentGetter
from src.crawler.spiders.carrier_eglv_multi import (
    CaptchaAnalyzer,
    BillMainInfoRoutingRule,
    FilingStatusRoutingRule,
    ReleaseStatusRoutingRule,
    ContainerStatusRoutingRule,
    BookingMainInfoRoutingRule,
)

EGLV_INFO_URL = "https://www.shipmentlink.com/servlet/TDB1_CargoTracking.do"


@dataclasses.dataclass
class ProxyOption:
    group: str
    session: str


logger = logging.getLogger("local-crawler-eglv")


class EglvContentGetter(PyppeteerContentGetter):
    MAX_CAPTCHA_RETRY = 3

    def __init__(self, proxy_manager: ProxyManager = None):
        super().__init__(proxy_manager)

    async def search_and_return(self, search_no, search_type, task_id):
        btn_value = "s_bl" if search_type == SHIPMENT_TYPE_MBL else "s_bk"

        try:
            await self.page.goto(EGLV_INFO_URL)
            await self.page.waitForSelector(f"input[value={btn_value}]")
            await self.page.waitForSelector("input#NO")
        except TimeoutError:
            raise LoadWebsiteTimeOutError(url=EGLV_INFO_URL)

        await self.page.click(f"input[value={btn_value}]")
        await self.page.type("input#NO", search_no)

        for _ in range(self.MAX_CAPTCHA_RETRY):
            await self.handle_captcha()
            self.page.on("dialog", lambda dialog: asyncio.ensure_future(self.close_dialog(dialog, task_id)))
            await self.page.click("#quick input[type=button]")
            try:
                await self.page.waitForSelector('table[cellpadding="2"]', {"timeout": 10000})
                await asyncio.sleep(1)
                content = await self.page.content()
                return content
            except TimeoutError:
                continue
        raise AntiCaptchaError

    async def handle_captcha(self):
        captcha_analyzer = CaptchaAnalyzer()
        element = await self.page.querySelector("div#captcha_div > img#captchaImg")
        get_base64_func = """(img) => {
                        var canvas = document.createElement("canvas");
                        canvas.width = 150;
                        canvas.height = 40;
                        var ctx = canvas.getContext("2d");
                        ctx.drawImage(img, 0, 0);
                        var dataURL = canvas.toDataURL("image/png");
                        return dataURL.replace(/^data:image\/(png|jpg);base64,/, "");
                    }
                    """
        captcha_base64 = await self.page.evaluate(get_base64_func, element)
        verification_code = captcha_analyzer.analyze_captcha(captcha_base64=captcha_base64).decode("utf-8")
        await self.page.type("div#captcha_div > input#captcha_input", verification_code)
        await asyncio.sleep(2)

    @staticmethod
    async def close_dialog(dialog, task_id):
        mbl_not_valid_msg = "B/L No. is not valid, please check again, thank you."
        booking_not_valid_msg = "Booking No. is not valid, please check again, thank you."
        if dialog.message == mbl_not_valid_msg or dialog.message == booking_not_valid_msg:
            raise DataNotFoundError(task_id)
        await dialog.accept()

    async def custom_info_page(self):
        await self.page.click("a[href=\"JavaScript:toggle('CustomsInfo');\"]")
        await asyncio.sleep(1)
        await self.page.click("a[href=\"JavaScript:getDispInfo('AMTitle','AMInfo');\"]")
        await self.page.waitForSelector("div#AMInfo table")
        await asyncio.sleep(2)
        div_ele = await self.page.querySelector("div#AMInfo")
        return await self.page.evaluate("(element) => element.outerHTML", div_ele)

    async def release_status_page(self):
        await self.page.click("a[href=\"JavaScript:getDispInfo('RlsStatusTitle','RlsStatusInfo');\"]")
        await self.page.waitForSelector("div#RlsStatusInfo table")
        await asyncio.sleep(2)
        div_ele = await self.page.querySelector("div#RlsStatusInfo")
        return await self.page.evaluate("(element) => element.outerHTML", div_ele)

    async def container_page(self, container_no):
        await self.page.click(f"a[href^=\"javascript:frmCntrMoveDetail('{container_no}')\"]")
        await asyncio.sleep(3)
        container_page = (await self.browser.pages())[-1]
        await stealth(container_page)
        await container_page.waitForSelector("table table")
        await asyncio.sleep(2)
        content = await container_page.content()
        await container_page.close()

        return content


class EglvLocalCrawler(BaseLocalCrawler):
    code = "EGLV"

    def __init__(self):
        super().__init__()
        self.content_getter = EglvContentGetter(proxy_manager=HydraproxyProxyManager(logger=logger))
        self._search_type = ""

    def start_crawler(self, task_ids: str, mbl_nos: str, booking_nos: str, container_nos: str):
        task_ids = task_ids.split(",")
        if mbl_nos:
            search_nos = mbl_nos.split(",")
            self._search_type = SHIPMENT_TYPE_MBL
            for search_no, task_id in zip(search_nos, task_ids):
                for item in self.handle_mbl(search_no, task_id):
                    yield item
        elif booking_nos:
            search_nos = booking_nos.split(",")
            self._search_type = SHIPMENT_TYPE_BOOKING
            for search_no, task_id in zip(search_nos, task_ids):
                for item in self.handle_booking(search_no, task_id):
                    yield item

    def handle_mbl(self, mbl_no, task_id):
        httptext = asyncio.get_event_loop().run_until_complete(
            self.content_getter.search_and_return(mbl_no, self._search_type, task_id)
        )
        response = self.get_response_selector(
            url=EGLV_INFO_URL, httptext=httptext, meta={"mbl_no": mbl_no, "task_id": task_id}
        )
        if self._is_search_no_invalid(response=response):
            raise DataNotFoundError(task_id=task_id)

        main_rule = BillMainInfoRoutingRule()

        for result in main_rule.handle(response):
            if isinstance(result, BaseCarrierItem):
                yield result
            elif isinstance(result, RequestOption):
                if result.rule_name == FilingStatusRoutingRule.name:
                    for filing_item in self.handle_filing_status(mbl_no, task_id):
                        yield filing_item

                elif result.rule_name == ReleaseStatusRoutingRule.name:
                    for release_item in self.handle_release_status(task_id):
                        yield release_item

                elif result.rule_name == ContainerStatusRoutingRule.name:
                    for container_item in self.handle_container_status(result.meta["container_no"], task_id):
                        yield container_item

    def handle_booking(self, search_no, task_id):
        httptext = asyncio.get_event_loop().run_until_complete(
            self.content_getter.search_and_return(search_no, self._search_type, task_id)
        )
        response = self.get_response_selector(
            url=EGLV_INFO_URL, httptext=httptext, meta={"booking_no": search_no, "task_id": task_id}
        )
        if self._is_search_no_invalid(response=response):
            raise DataNotFoundError(task_id=task_id)

        rule = BookingMainInfoRoutingRule()

        for result in rule.handle(response):
            if isinstance(result, BaseCarrierItem):
                yield result
            elif isinstance(result, RequestOption) and result.rule_name == ContainerStatusRoutingRule.name:
                for container_item in self.handle_container_status(result.meta["container_no"], task_id):
                    yield container_item

    def handle_filing_status(self, mbl_no, task_id):
        httptext = asyncio.get_event_loop().run_until_complete(self.content_getter.custom_info_page())
        response = self.get_response_selector(
            url=EGLV_INFO_URL, httptext=httptext, meta={"mbl_no": mbl_no, "task_id": task_id}
        )
        rule = FilingStatusRoutingRule()

        for item in rule.handle(response):
            yield item

    def handle_release_status(self, task_id):
        httptext = asyncio.get_event_loop().run_until_complete(self.content_getter.release_status_page())
        response = self.get_response_selector(url=EGLV_INFO_URL, httptext=httptext, meta={"task_id": task_id})
        rule = ReleaseStatusRoutingRule()

        for item in rule.handle(response):
            yield item

    def handle_container_status(self, container_no, task_id):
        httptext = asyncio.get_event_loop().run_until_complete(self.content_getter.container_page(container_no))
        response = self.get_response_selector(
            url=EGLV_INFO_URL, httptext=httptext, meta={"container_no": container_no, "task_id": task_id}
        )
        rule = ContainerStatusRoutingRule()

        for item in rule.handle(response):
            yield item

    @staticmethod
    def _is_search_no_invalid(response):
        message_under_search_table = response.css("table table tr td.f12wrdb1::text").get()
        if isinstance(message_under_search_table, str):
            message_under_search_table = message_under_search_table.strip()
        mbl_invalid_message = (
            "No information on B/L No., please enter a valid B/L No. or contact our offices for assistance."
        )
        boooking_invalid_message = (
            "No information on Booking No., please enter a valid Booking No. or contact our offices for assistance."
        )

        if message_under_search_table == mbl_invalid_message or message_under_search_table == boooking_invalid_message:
            return True

        return False
