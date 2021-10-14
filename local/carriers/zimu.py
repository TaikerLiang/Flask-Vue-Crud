import dataclasses
import random
import asyncio

import scrapy
from pyppeteer import launch, logging
from pyppeteer.errors import TimeoutError
from urllib3.exceptions import ReadTimeoutError

from local.core import BaseLocalCrawler
from local.proxy import ApifyProxyManager, ProxyManager
from local.exceptions import AccessDeniedError, DataNotFoundError
from src.crawler.core_carrier.exceptions import LoadWebsiteTimeOutError
from src.crawler.spiders.carrier_zimu import MainInfoRoutingRule


@dataclasses.dataclass
class ProxyOption:
    group: str
    session: str


class ZimuContentGetter:
    def __init__(self, proxy_manager: ProxyManager):
        logging.disable(logging.DEBUG)
        self._is_first = True
        self._proxy_manager = proxy_manager

        # prefs = {"profile.managed_default_content_settings.images": 2}

    async def launch_browser(self):
        browser_args = [
            "--no-sandbox",
            "--disable-gpu",
            "--disable-dev-shm-usage",
            "--disable-blink-features",
            "--disable-notifications",
            "--disable-extensions",
            "--disable-plugins",
            "--disable-infobars",
            "--enable-javascript",
            "--window-size=1920,1080",
            f"--proxy-server={self._proxy_manager.PROXY_DOMAIN}",
        ]

        self._proxy_manager.renew_proxy()
        self._browser = await launch(headless=False, slowMo=20, args=browser_args)
        self._page = await self._browser.newPage()

        auth = {
            "username": self._proxy_manager._proxy_username,
            "password": self._proxy_manager.PROXY_PASSWORD,
        }
        await self._page.authenticate(auth)

        await self._page.setUserAgent(
            f"Mozilla/5.0 (Macintosh; Intel Mac OS X 11_1_0) AppleWebKit/537.36 (KHTML, like Gecko) "
            f"Chrome/88.0.4324.96 Safari/537.36"
        )

    async def _accept_cookie(self):
        accept_btn_css = "#onetrust-accept-btn-handler"
        try:
            await self._page.waitForSelector(accept_btn_css, timeout=5000)
        except (TimeoutError, ReadTimeoutError):
            raise LoadWebsiteTimeOutError(url="https://www.zim.com/tools/track-a-shipment")

        await asyncio.sleep(1)
        await self._page.click(accept_btn_css)

    async def search_and_return(self, mbl_no: str):
        await self._page.goto("https://www.zim.com/tools/track-a-shipment", timeout=40000)

        if self._is_first:
            self._is_first = False
            await self._accept_cookie()
            await self._page.hover("a.location")

        for i in range(random.randint(1, 3)):
            await self.move_mouse_to_random_position()

        search_bar = "input[name='consnumber']"
        await self._page.hover(search_bar)
        await self._page.click(search_bar)
        await asyncio.sleep(2)
        await self._page.type(search_bar, text=mbl_no)
        await asyncio.sleep(2)
        await self._page.keyboard.press("Enter")
        await asyncio.sleep(20)
        await self.scroll_down()

        page_source = await self._page.content()
        return page_source

    async def move_mouse_to_random_position(self):
        x = random.randint(0, 600)
        y = random.randint(0, 400)
        await self._page.mouse.move(x, y)
        await asyncio.sleep(0.5)

    async def scroll_down(self):
        await self._page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
        await asyncio.sleep(2)

    def quit(self):
        asyncio.get_event_loop().run_until_complete(self._browser.close())


class ZimuLocalCrawler(BaseLocalCrawler):
    code = "ZIMU"

    def __init__(self):
        super().__init__()
        self.content_getter = ZimuContentGetter(proxy_manager=ApifyProxyManager(session="zimu", logger=None))

    def start_crawler(self, task_ids: str, mbl_nos: str, booking_nos: str, container_nos: str):
        task_ids = task_ids.split(",")
        mbl_nos = mbl_nos.split(",")
        id_mbl_map = {mbl_no: task_id for task_id, mbl_no in zip(task_ids, mbl_nos)}

        asyncio.get_event_loop().run_until_complete(self.content_getter.launch_browser())
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
