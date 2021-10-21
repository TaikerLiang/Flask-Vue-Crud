import dataclasses
import asyncio

import scrapy
from pyppeteer import launch, logging
from urllib3.exceptions import ReadTimeoutError

from local.core import BaseLocalCrawler
from src.crawler.core_carrier.exceptions import LoadWebsiteTimeOutError
from src.crawler.core_carrier.base import SHIPMENT_TYPE_MBL, SHIPMENT_TYPE_BOOKING
from src.crawler.core_carrier.exceptions import (
    LoadWebsiteTimeOutError,
    CarrierInvalidSearchNoError,
    CARRIER_RESULT_STATUS_ERROR,
)
from src.crawler.core_carrier.items import ExportErrorData
from src.crawler.spiders.carrier_mscu import MainRoutingRule

MSCU_URL = "https://www.msc.com/track-a-shipment?agencyPath=twn"


@dataclasses.dataclass
class ProxyOption:
    group: str
    session: str


class MscuContentGetter:
    def __init__(self):
        logging.disable(logging.DEBUG)
        self._search_type = None
        self._browser = None
        self._page = None

    async def launch_and_go(self):
        browser_args = [
            "--no-sandbox",
            "--disable-gpu",
            "--disable-blink-features",
            "--disable-infobars",
            "--window-size=1920,1080",
        ]
        self._browser = await launch(headless=True, slowMo=20, args=browser_args)
        self._page = await self._browser.newPage()
        await self._page.setViewport({"width": 1920, "height": 1080})
        await self._page.setUserAgent(
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.71 Safari/537.36"
        )
        await self._page.setCookie(
            {"url": MSCU_URL, "name": "newsletter-signup-cookie", "value": "temp-hidden", "domain": "www.msc.com"}
        )
        await self._page.setCookie(
            {
                "url": MSCU_URL,
                "name": "OptanonAlertBoxClosed",
                "value": "2021-10-21T03:04:49.663Z",
                "domain": ".msc.com",
            }
        )

        await self._page.goto(MSCU_URL, options={"timeout": 60000})
        await asyncio.sleep(1)

    async def search(self, search_no, search_type):
        type_dropdown = "#ctl00_ctl00_plcMain_plcMain_TrackSearch_fldTrackingType_DropDownField"
        await self._page.waitForSelector(type_dropdown)
        if search_type == SHIPMENT_TYPE_MBL:
            await self._page.select(type_dropdown, "containerbilloflading")
        elif search_type == SHIPMENT_TYPE_BOOKING:
            await self._page.select(type_dropdown, "bookingnumber")

        await self._page.type("#ctl00_ctl00_plcMain_plcMain_TrackSearch_txtBolSearch_TextField", text=search_no)
        await asyncio.sleep(0.5)
        await self._page.click("#ctl00_ctl00_plcMain_plcMain_TrackSearch_hlkSearch")

        return await self._page.content()

    def quit(self):
        asyncio.get_event_loop().run_until_complete(self._browser.close())


class MscuLocalCrawler(BaseLocalCrawler):
    code = "MSCU"

    def __init__(self):
        super().__init__()
        self._search_type = ""
        self._search_nos = []
        self.content_getter = MscuContentGetter()

    def start_crawler(self, task_ids: str, mbl_nos: str, booking_nos: str, container_nos: str):
        asyncio.get_event_loop().run_until_complete(self.content_getter.launch_and_go())

        task_ids = task_ids.split(",")
        if mbl_nos:
            self._search_nos = mbl_nos.split(",")
            self._search_type = SHIPMENT_TYPE_MBL
        elif booking_nos:
            self._search_nos = booking_nos.split(",")
            self._search_type = SHIPMENT_TYPE_BOOKING

        id_mbl_map = {search_no: task_id for task_id, search_no in zip(task_ids, self._search_nos)}
        for search_no, task_id in id_mbl_map.items():
            try:
                res = asyncio.get_event_loop().run_until_complete(
                    self.content_getter.search(search_no=search_no, search_type=self._search_type)
                )
                response = scrapy.Selector(text=res)
                main_rule = MainRoutingRule(search_type=self._search_type)
                for item in main_rule.handle(response=response):
                    item["task_id"] = task_id
                    yield item
            except ReadTimeoutError:
                raise LoadWebsiteTimeOutError(url=MSCU_URL)
            except CarrierInvalidSearchNoError:
                if self._search_type == SHIPMENT_TYPE_MBL:
                    yield ExportErrorData(
                        task_id=task_id,
                        mbl_no=search_no,
                        status=CARRIER_RESULT_STATUS_ERROR,
                        detail="Data was not found",
                    )
                elif self._search_type == SHIPMENT_TYPE_BOOKING:
                    ExportErrorData(
                        task_id=task_id,
                        booking_no=search_no,
                        status=CARRIER_RESULT_STATUS_ERROR,
                        detail="Data was not found",
                    )
                continue
