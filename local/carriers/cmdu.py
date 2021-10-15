import dataclasses
import asyncio

from scrapy import Selector, Request
from scrapy.http import TextResponse
from pyppeteer import launch, logging
from pyppeteer.errors import TimeoutError, ElementHandleError

from local.core import BaseLocalCrawler
from crawler.core_carrier.request_helpers import RequestOption
from crawler.core_carrier.items import BaseCarrierItem
from src.crawler.core_carrier.base import SHIPMENT_TYPE_MBL, SHIPMENT_TYPE_BOOKING
from src.crawler.core_carrier.exceptions import LoadWebsiteTimeOutError
from src.crawler.core_carrier.anlc_aplu_cmdu_share_spider import FirstTierRoutingRule, ContainerStatusRoutingRule

CMDU_BASE_URL = 'https://www.cma-cgm.com/ebusiness/tracking'


@dataclasses.dataclass
class ProxyOption:
    group: str
    session: str


class ContentGetter:
    def __init__(self):
        logging.disable(logging.DEBUG)
        self._browser = None

    async def launch_browser(self):
        browser_args = [
            "--no-sandbox",
            "--disable-gpu",
            "--disable-blink-features",
            "--disable-infobars",
            "--window-size=1920,1080",
        ]
        self._browser = await launch(headless=True, dumpio=True, slowMo=20, defaultViewport=None, args=browser_args)

    async def search(self, search_no):
        page = await self._browser.newPage()
        await page.setUserAgent(
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.71 Safari/537.36"
        )
        try:
            await asyncio.gather(
                page.waitForSelector("#Reference"),
                page.goto(CMDU_BASE_URL),
            )
            await page.type('#Reference', search_no)
            await asyncio.gather(
                page.waitForSelector("div > h1"),
                page.click('#btnTracking')
            )
        except TimeoutError:
            raise LoadWebsiteTimeOutError

        content = await page.content()
        await page.close()
        return content

    async def close(self):
        await self._browser.close()


class CmduLocalCrawler(BaseLocalCrawler):
    code = "CMDU"

    def __init__(self):
        super().__init__()
        self.content_getter = ContentGetter()
        self._search_type = ""
        self.driver = ContentGetter()

    def start_crawler(self, task_ids: str, mbl_nos: str, booking_nos: str, container_nos: str):
        task_ids = task_ids.split(",")
        search_nos = []
        if mbl_nos:
            search_nos = mbl_nos.split(",")
            self._search_type = SHIPMENT_TYPE_MBL
        elif booking_nos:
            search_nos = booking_nos.split(",")
            self._search_type = SHIPMENT_TYPE_BOOKING

        id_search_map = {search_no: task_id for task_id, search_no in zip(task_ids, search_nos)}
        for search_no, task_id in id_search_map.items():
            for item in self.handle(search_no, task_id):
                yield item

    def handle(self, search_no, task_id):
        asyncio.get_event_loop().run_until_complete(self.driver.launch_browser())
        httptext = asyncio.get_event_loop().run_until_complete(self.driver.search(search_no=search_no))
        response = TextResponse(
            url=CMDU_BASE_URL,
            encoding='utf-8',
            body=httptext,
            request=Request(
                url=CMDU_BASE_URL,
                meta={
                    "search_no": search_no,
                    "base_url": CMDU_BASE_URL,
                    "task_id": task_id,
                },
            )
        )
        first_tier_rule = FirstTierRoutingRule(search_type=self._search_type)
        container_rule = ContainerStatusRoutingRule()
        for result in first_tier_rule.handle(response):
            if isinstance(result, BaseCarrierItem):
                yield result
            elif isinstance(result, RequestOption):
                container_no = result.meta['container_no']
                httptext = asyncio.get_event_loop().run_until_complete(self.driver.search(search_no=container_no))
                response = TextResponse(
                    url=CMDU_BASE_URL,
                    encoding='utf-8',
                    body=httptext,
                    request=Request(
                        url=CMDU_BASE_URL,
                        meta={
                            "search_no": search_no,
                            "container_no": container_no,
                            "task_id": task_id,
                        },
                    )
                )
                for container_item in container_rule.handle(response):
                    yield container_item
        asyncio.get_event_loop().run_until_complete(self.driver.close())
