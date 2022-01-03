import dataclasses
import random
import asyncio
import logging

import scrapy
from pyppeteer.errors import TimeoutError
from urllib3.exceptions import ReadTimeoutError

from local.core import BaseLocalCrawler
from local.exceptions import AccessDeniedError, DataNotFoundError
from src.crawler.core.proxy import HydraproxyProxyManager, ProxyManager
from src.crawler.core_carrier.exceptions import LoadWebsiteTimeOutError
from src.crawler.core.pyppeteer import PyppeteerContentGetter
from src.crawler.spiders.carrier_zimu import MainInfoRoutingRule


@dataclasses.dataclass
class ProxyOption:
    group: str
    session: str


logger = logging.getLogger("local-crawler-zimu")


class ZimuContentGetter(PyppeteerContentGetter):
    def __init__(self, proxy_manager: ProxyManager = None):
        super().__init__(proxy_manager)

    async def _accept_cookie(self):
        accept_btn_css = "#onetrust-accept-btn-handler"
        try:
            await self.page.waitForSelector(accept_btn_css, timeout=5000)
        except (TimeoutError, ReadTimeoutError):
            raise LoadWebsiteTimeOutError(url="https://www.zim.com/tools/track-a-shipment")

        await asyncio.sleep(1)
        await self.page.click(accept_btn_css)

    async def search_and_return(self, mbl_no: str):
        await self.page.goto("https://api.myip.com/")
        await asyncio.sleep(5)
        await self.page.goto("https://www.zim.com/tools/track-a-shipment", timeout=70000)

        if self._is_first:
            self._is_first = False
            await self._accept_cookie()
            await self.page.hover("a.location")

        for i in range(random.randint(1, 3)):
            await self.move_mouse_to_random_position()

        search_bar = "input[name='consnumber']"
        await self.page.hover(search_bar)

        await self.page.click(search_bar)
        await asyncio.sleep(2)
        await self.page.type(search_bar, text=mbl_no)
        await asyncio.sleep(2)
        await self.page.keyboard.press("Enter")
        await asyncio.sleep(30)
        await self.scroll_down()

        page_source = await self.page.content()
        return page_source


class ZimuLocalCrawler(BaseLocalCrawler):
    code = "ZIMU"

    def __init__(self):
        super().__init__()
        self.content_getter = ZimuContentGetter(proxy_manager=HydraproxyProxyManager(logger=logger))

    def start_crawler(self, task_ids: str, mbl_nos: str, booking_nos: str, container_nos: str):
        task_ids = task_ids.split(",")
        mbl_nos = mbl_nos.split(",")
        id_mbl_map = {mbl_no: task_id for task_id, mbl_no in zip(task_ids, mbl_nos)}

        for mbl_no, task_id in id_mbl_map.items():
            yield {"task_id": task_id}
            res = asyncio.get_event_loop().run_until_complete(self.content_getter.search_and_return(mbl_no=mbl_no))
            response = scrapy.Selector(text=res)

            alter_msg = response.xpath("/html/body/h1")
            if alter_msg:
                print("alter_msg.extract()", alter_msg.extract())
                raise AccessDeniedError()

            if self._is_mbl_no_invalid(response=response):
                raise DataNotFoundError(task_id=task_id)

            main_rule = MainInfoRoutingRule()
            main_rule.handle_item(response=response)

            for item in main_rule.handle_item(response=response):
                yield item

    @staticmethod
    def _is_mbl_no_invalid(response) -> bool:
        no_result_information = response.css("section#noResult p")
        if no_result_information:
            return True
