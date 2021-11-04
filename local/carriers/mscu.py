import dataclasses
import asyncio

from pyppeteer import logging
from urllib3.exceptions import ReadTimeoutError

from local.core import BaseLocalCrawler
from local.proxy import ProxyManager
from src.crawler.core.pyppeteer import PyppeteerContentGetter
from src.crawler.core_carrier.exceptions import LoadWebsiteTimeOutError
from src.crawler.core_carrier.base import SHIPMENT_TYPE_MBL, SHIPMENT_TYPE_BOOKING
from src.crawler.core_carrier.exceptions import LoadWebsiteTimeOutError
from src.crawler.spiders.carrier_mscu import MainRoutingRule

MSCU_URL = "https://www.msc.com/track-a-shipment?agencyPath=twn"


@dataclasses.dataclass
class ProxyOption:
    group: str
    session: str


class MscuContentGetter(PyppeteerContentGetter):
    def __init__(self, proxy_manager: ProxyManager = None):
        super().__init__(proxy_manager)
        logging.disable(logging.DEBUG)
        self._search_type = None

    async def set_cookies(self):
        cookies = [
            {"url": MSCU_URL, "name": "newsletter-signup-cookie", "value": "temp-hidden", "domain": "www.msc.com"},
            {
                "url": MSCU_URL,
                "name": "OptanonAlertBoxClosed",
                "value": "2021-10-21T03:04:49.663Z",
                "domain": ".msc.com",
            },
        ]
        await self.page.setCookie(*cookies)

    async def search(self, search_no, search_type):
        await self.set_cookies()
        await self.page.goto(MSCU_URL, options={"timeout": 60000})
        await asyncio.sleep(1)

        type_dropdown = "#ctl00_ctl00_plcMain_plcMain_TrackSearch_fldTrackingType_DropDownField"
        await self.page.waitForSelector(type_dropdown)
        if search_type == SHIPMENT_TYPE_MBL:
            await self.page.select(type_dropdown, "containerbilloflading")
        elif search_type == SHIPMENT_TYPE_BOOKING:
            await self.page.select(type_dropdown, "bookingnumber")

        await self.page.type("#ctl00_ctl00_plcMain_plcMain_TrackSearch_txtBolSearch_TextField", text=search_no)
        await asyncio.sleep(0.5)
        await self.page.click("#ctl00_ctl00_plcMain_plcMain_TrackSearch_hlkSearch")
        await self.page.waitForNavigation()
        return await self.page.content()


class MscuLocalCrawler(BaseLocalCrawler):
    code = "MSCU"

    def __init__(self):
        super().__init__()
        self._search_type = ""
        self._search_nos = []
        self.content_getter = MscuContentGetter()

    def start_crawler(self, task_ids: str, mbl_nos: str, booking_nos: str, container_nos: str):
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

                response = self.get_response_selector(url=MSCU_URL, httptext=res, meta={"search_no": search_no})
                main_rule = MainRoutingRule(search_type=self._search_type)
                for item in main_rule.handle(response=response):
                    item["task_id"] = task_id
                    yield item
            except ReadTimeoutError:
                raise LoadWebsiteTimeOutError(url=MSCU_URL)
