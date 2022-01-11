from typing import Any
import random
import asyncio
import logging

from pyppeteer import connection, launch, launcher
from pyppeteer_stealth import stealth
import websockets.client

from crawler.core.defines import BaseContentGetter


class PyppeteerContentGetter(BaseContentGetter):
    def __init__(self, proxy_manager: None, is_headless: bool = False):
        self._is_first = True
        self.proxy_manager = proxy_manager
        self.browser = None
        self.page = None

        self._patch_pyppeteer()
        asyncio.get_event_loop().run_until_complete(self.launch_browser(is_headless=is_headless))

    async def launch_browser(self, is_headless: bool):
        browser_args = [
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-blink-features",
            "--enable-javascript",
            "--window-size=1920,1080",
            # "--start-maximized",
        ]
        default_viewport = {
            "width": 1200,
            "height": 700,
        }

        auth = {}
        if self.proxy_manager:
            browser_args.append(f"--proxy-server=http://{self.proxy_manager.PROXY_DOMAIN}")
            self.proxy_manager.renew_proxy()
            auth = {
                "username": self.proxy_manager.proxy_username,
                "password": self.proxy_manager.proxy_password,
            }

        pyppeteer_logger = logging.getLogger("pyppeteer")
        pyppeteer_logger.setLevel(logging.WARNING)

        self.browser = await launch(headless=is_headless, args=browser_args, defaultViewport=default_viewport)
        pages = await self.browser.pages()
        self.page = pages[0]

        await stealth(self.page)

        if auth:
            await self.page.authenticate(auth)

        await self.page.evaluate("""() =>{ Object.defineProperties(navigator,{ webdriver:{ get: () => false } }) }""")

        await self.page.setUserAgent(
            f"Mozilla/5.0 (Macintosh; Intel Mac OS X 11_1_0) AppleWebKit/537.36 (KHTML, like Gecko) "
            f"Chrome/88.0.4324.96 Safari/537.36"
        )

    async def move_mouse_to_random_position(self):
        x = random.randint(0, 600)
        y = random.randint(0, 400)
        await self.page.mouse.move(x, y)
        await asyncio.sleep(0.5)

    async def scroll_down(self):
        await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
        await asyncio.sleep(2)

    def quit(self):
        asyncio.get_event_loop().run_until_complete(self.browser.close())

    def _patch_pyppeteer(self):
        class PatchedConnection(connection.Connection):  # type: ignore
            def __init__(self, *args: Any, **kwargs: Any) -> None:
                super().__init__(*args, **kwargs)
                # the _ws argument is not yet connected, can simply be replaced with another
                # with better defaults.
                self._ws = websockets.client.connect(
                    self._url,
                    loop=self._loop,
                    # the following parameters are all passed to WebSocketCommonProtocol
                    # which markes all three as Optional, but connect() doesn't, hence the liberal
                    # use of type: ignore on these lines.
                    # fixed upstream but not yet released, see aaugustin/websockets#93ad88
                    max_size=None,  # type: ignore
                    ping_interval=None,  # type: ignore
                    ping_timeout=None,  # type: ignore
                )

        connection.Connection = PatchedConnection
        # also imported as a  global in pyppeteer.launcher
        launcher.Connection = PatchedConnection
