import dataclasses
import asyncio
import logging

from scrapy import Request
from scrapy.http import TextResponse
from pyppeteer.errors import TimeoutError, ElementHandleError

from local.core import BaseLocalCrawler
from local.proxy import HydraproxyProxyManager, ProxyManager
from crawler.core.pyppeteer import PyppeteerContentGetter
from crawler.core_carrier.request_helpers import RequestOption
from crawler.core_carrier.items import BaseCarrierItem
from crawler.core_carrier.base import SHIPMENT_TYPE_MBL, SHIPMENT_TYPE_BOOKING
from crawler.core_carrier.exceptions import LoadWebsiteTimeOutError
from crawler.core_carrier.anlc_aplu_cmdu_share_spider import FirstTierRoutingRule, ContainerStatusRoutingRule

CMDU_BASE_URL = 'https://www.cma-cgm.com/ebusiness/tracking'


@dataclasses.dataclass
class ProxyOption:
    group: str
    session: str


logger = logging.getLogger("local-crawler-cmdu")


class ContentGetter(PyppeteerContentGetter):
    def __init__(self, proxy_manager: ProxyManager = None):
        super().__init__(proxy_manager)

    async def search(self, search_no):
        try:
            await asyncio.sleep(3)
            await self.page.goto(CMDU_BASE_URL, {"timeout": 60000})
        except TimeoutError:
            raise LoadWebsiteTimeOutError(url=CMDU_BASE_URL)
        await self.page.type('#Reference', search_no)
        await asyncio.sleep(3)
        await self.page.click('#btnTracking')
        await asyncio.sleep(3)
        await self.page.waitForSelector("div > h1"),
        await asyncio.sleep(3)

        content = await self.page.content()
        return content


class CmduLocalCrawler(BaseLocalCrawler):
    code = "CMDU"

    def __init__(self):
        super().__init__()
        self.content_getter = ContentGetter()
        self._search_type = ""

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
        httptext = asyncio.get_event_loop().run_until_complete(self.content_getter.search(search_no=search_no))
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
                httptext = asyncio.get_event_loop().run_until_complete(self.content_getter.search(search_no=container_no))
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
