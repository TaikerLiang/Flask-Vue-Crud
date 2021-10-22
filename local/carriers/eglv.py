import dataclasses
import asyncio

from scrapy import Request
from scrapy.http import TextResponse
from pyppeteer import launch, logging
from pyppeteer.errors import TimeoutError, ElementHandleError

from local.core import BaseLocalCrawler
from crawler.core_carrier.request_helpers import RequestOption
from crawler.core_carrier.items import BaseCarrierItem
from src.crawler.core_carrier.base import SHIPMENT_TYPE_MBL, SHIPMENT_TYPE_BOOKING
from src.crawler.core_carrier.exceptions import LoadWebsiteTimeOutError, AntiCaptchaError, CarrierInvalidSearchNoError
from src.crawler.spiders.carrier_eglv_multi import (
    CaptchaAnalyzer,
    BillMainInfoRoutingRule,
    FilingStatusRoutingRule,
    ReleaseStatusRoutingRule,
    ContainerStatusRoutingRule,
    BookingMainInfoRoutingRule,
)

EGLV_INFO_URL = 'https://www.shipmentlink.com/servlet/TDB1_CargoTracking.do'


@dataclasses.dataclass
class ProxyOption:
    group: str
    session: str


class EglvContentGetter:
    MAX_CAPTCHA_RETRY = 3

    def __init__(self):
        logging.disable(logging.DEBUG)
        self._browser = None
        self._page = None
        self._captcha_analyzer = CaptchaAnalyzer()

    async def launch_browser(self):
        browser_args = [
            "--no-sandbox",
            "--disable-gpu",
            "--disable-blink-features",
            "--disable-infobars",
            "--window-size=1920,1080",
        ]
        default_viewport = {
            "width": 1920,
            "height": 1080,
        }
        self._browser = await launch(headless=True, dumpio=True, slowMo=20, defaultViewport=default_viewport,
                                     args=browser_args)

    async def search_and_return(self, search_no, search_type):
        self._page = await self._browser.newPage()
        await self._page.setUserAgent(
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.71 Safari/537.36"
        )
        btn_value = "s_bl" if search_type == SHIPMENT_TYPE_MBL else "s_bk"

        try:
            await self._page.goto(EGLV_INFO_URL)
            await self._page.waitForSelector(f"input[value={btn_value}]")
            await self._page.waitForSelector("input#NO")
        except TimeoutError:
            raise LoadWebsiteTimeOutError(url=EGLV_INFO_URL)

        await self._page.click(f"input[value={btn_value}]")
        await self._page.type("input#NO", search_no)

        for _ in range(self.MAX_CAPTCHA_RETRY):
            await self.handle_captcha()
            self._page.on('dialog', lambda dialog: asyncio.ensure_future(self.close_dialog(dialog)))
            await self._page.click("#quick input[type=button]")
            try:
                await self._page.waitForSelector("table[cellpadding=\"2\"]", {"timeout": 10000})
                content = await self._page.content()
                return content
            except TimeoutError:
                continue
        raise AntiCaptchaError

    async def handle_captcha(self):
        element = await self._page.querySelector("div#captcha_div > img#captchaImg")
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
        captcha_base64 = await self._page.evaluate(get_base64_func, element)
        verification_code = self._captcha_analyzer.analyze_captcha(captcha_base64=captcha_base64).decode("utf-8")
        await self._page.type("div#captcha_div > input#captcha_input", verification_code)

    @staticmethod
    async def close_dialog(dialog):
        if dialog.message == "B/L No. is not valid, please check again, thank you.":
            raise CarrierInvalidSearchNoError
        await dialog.accept()

    async def custom_info_page(self):
        await self._page.click("a[href=\"JavaScript:toggle(\'CustomsInfo\');\"]")
        await asyncio.sleep(1)
        await self._page.click("a[href=\"JavaScript:getDispInfo(\'AMTitle\',\'AMInfo\');\"]")
        await asyncio.sleep(1)
        div_ele = await self._page.querySelector("div#AMInfo")
        return await self._page.evaluate("(element) => element.outerHTML", div_ele)

    async def release_status_page(self):
        await self._page.click("a[href=\"JavaScript:getDispInfo(\'RlsStatusTitle\',\'RlsStatusInfo\');\"]")
        await asyncio.sleep(1)
        div_ele = await self._page.querySelector("div#RlsStatusInfo")
        return await self._page.evaluate("(element) => element.outerHTML", div_ele)

    async def container_page(self, container_no):
        await self._page.click(f"a[href^=\"javascript:frmCntrMoveDetail(\'{container_no}\')\"]")
        await asyncio.sleep(1)
        container_page = (await self._browser.pages())[-1]
        await container_page.waitForSelector("table table")
        content = await container_page.content()
        await container_page.close()

        return content

    async def close(self):
        await self._browser.close()


class EglvLocalCrawler(BaseLocalCrawler):
    code = "EGLV"

    def __init__(self):
        super().__init__()
        self.content_getter = EglvContentGetter()
        self._search_type = ""

    def start_crawler(self, task_ids: str, mbl_nos: str, booking_nos: str, container_nos: str):
        asyncio.get_event_loop().run_until_complete(self.content_getter.launch_browser())

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

        asyncio.get_event_loop().run_until_complete(self.content_getter.close())

    def handle_mbl(self, mbl_no, task_id):
        httptext = asyncio.get_event_loop().run_until_complete(
            self.content_getter.search_and_return(mbl_no, self._search_type))
        response = self.get_response_selector(httptext, meta={"mbl_no": mbl_no, "task_id": task_id})
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
                    for container_item in self.handle_container_status(result.meta['container_no'], task_id):
                        yield container_item

    def handle_booking(self, search_no, task_id):
        httptext = asyncio.get_event_loop().run_until_complete(
            self.content_getter.search_and_return(search_no, self._search_type))
        response = self.get_response_selector(httptext, meta={"booking_no": search_no, "task_id": task_id})
        rule = BookingMainInfoRoutingRule()

        for result in rule.handle(response):
            if isinstance(result, BaseCarrierItem):
                yield result
            elif isinstance(result, RequestOption) and result.rule_name == ContainerStatusRoutingRule.name:
                for container_item in self.handle_container_status(result.meta['container_no'], task_id):
                    yield container_item

    def handle_filing_status(self, mbl_no, task_id):
        httptext = asyncio.get_event_loop().run_until_complete(
            self.content_getter.custom_info_page())
        response = self.get_response_selector(httptext, meta={"mbl_no": mbl_no, "task_id": task_id})
        rule = FilingStatusRoutingRule()

        for item in rule.handle(response):
            yield item

    def handle_release_status(self, task_id):
        httptext = asyncio.get_event_loop().run_until_complete(
            self.content_getter.release_status_page())
        response = self.get_response_selector(httptext, meta={"task_id": task_id})
        rule = ReleaseStatusRoutingRule()

        for item in rule.handle(response):
            yield item

    def handle_container_status(self, container_no, task_id):
        httptext = asyncio.get_event_loop().run_until_complete(self.content_getter.container_page(container_no))
        response = self.get_response_selector(httptext, meta={"container_no": container_no, "task_id": task_id})
        rule = ContainerStatusRoutingRule()

        for item in rule.handle(response):
            yield item

    @staticmethod
    def get_response_selector(httptext, meta):
        return TextResponse(
            url=EGLV_INFO_URL,
            body=httptext,
            encoding='utf-8',
            request=Request(
                url=EGLV_INFO_URL,
                meta=meta,
            )
        )
