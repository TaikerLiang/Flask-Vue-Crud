import random
import asyncio

from pyppeteer import launch
from pyppeteer_stealth import stealth


class PyppeteerContentGetter:
    def __init__(self, proxy_manager: None):
        self._is_first = True
        self.proxy_manager = proxy_manager
        self.browser = None
        self.page = None

        asyncio.get_event_loop().run_until_complete(self.launch_browser(is_headless=False))

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
            "width": 1920,
            "height": 1080,
        }

        auth = {}
        if self.proxy_manager:
            browser_args.append(f"--proxy-server=http://{self.proxy_manager.PROXY_DOMAIN}")
            self.proxy_manager.renew_proxy()
            auth = {
                "username": self.proxy_manager.proxy_username,
                "password": self.proxy_manager.proxy_password,
            }

        self.browser = await launch(headless=is_headless, args=browser_args, defaultViewport=default_viewport)
        self.page = await self.browser.newPage()

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
