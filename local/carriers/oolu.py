import base64
from io import BytesIO
import logging
import os
import time
from typing import Dict

from PIL import Image
import cv2
import numpy as np
from scrapy import Selector
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from crawler.core.base_new import SEARCH_TYPE_BOOKING, SEARCH_TYPE_MBL
from crawler.core.exceptions_new import AccessDeniedError, MaxRetryError
from crawler.core.proxy import HydraproxyProxyManager
from local.config import PROFILE_PATH
from local.core import BaseLocalCrawler
from src.crawler.core.selenium import ChromeContentGetter
from src.crawler.spiders.carrier_oolu_multi import CargoTrackingRule

logger = logging.getLogger("local-crawler-oolu")


class ContentGetter(ChromeContentGetter):
    MAX_SEARCH_TIMES = 10

    def __init__(self, proxy_manager, is_headless):
        self.block_urls = [
            "https://www.oocl.com/Style%20Library/revamp/images/flexslider_depot.jpg",
            "https://www.oocl.com/Style%20Library/revamp/images/*.png",
            # "https://moc.oocl.com/app/skin/mcc_oocl/images/*.gif",
            # "https://www.oocl.com/Style%20Library/revamp/Images/*.svg",
            "https://moc.oocl.com/admin/scripts/jquery-1.8.0.js",
            "https://www.google-analytics.com/analytics.js",
            "https://moc.oocl.com/admin/common/xss.js",
            "https://ca.cargosmart.ai/js/analytics.client.core.js",
        ]

        super().__init__(
            proxy_manager=proxy_manager, is_headless=is_headless, block_urls=self.block_urls, profile_path=PROFILE_PATH
        )

        logging.getLogger("seleniumwire").setLevel(logging.ERROR)
        logging.getLogger("hpack").setLevel(logging.INFO)

        self._driver.set_page_load_timeout(120)
        self._first = True
        self._search_count = 0

    def goto(self):
        self._driver.get("https://www.oocl.com/eng/ourservices/eservices/cargotracking/Pages/cargotracking.aspx")
        time.sleep(3)

    def search_and_return(self, info_pack: Dict):
        search_no = info_pack["search_no"]
        search_type = info_pack["search_type"]
        if self._first:
            self.goto()
        self.search(search_no=search_no, search_type=search_type)
        time.sleep(7)
        windows = self._driver.window_handles
        self._driver.switch_to.window(windows[1])  # windows[1] is new page
        time.sleep(30)

        if self._is_blocked(response=Selector(text=self._driver.page_source)):
            raise AccessDeniedError(**info_pack, reason="Blocked during searching")

        if self._pass_verification_or_not():
            self._handle_with_slide(info_pack=info_pack)
            time.sleep(10)

        self._search_count = 0
        self._first = False
        return self._driver.page_source

    def search_again_and_return(self, info_pack: Dict):
        self._driver.close()

        self._search_count += 1
        if self._search_count > self.MAX_SEARCH_TIMES:
            raise MaxRetryError(**info_pack, reason=f"Retry search more than {self.MAX_SEARCH_TIMES} times")

        # jump back to origin window
        windows = self._driver.window_handles
        assert len(windows) == 1
        self._driver.switch_to.window(windows[0])

        return self.search_and_return(info_pack=info_pack)

    def get_window_handles(self):
        return self._driver.window_handles

    def switch_to_first(self):
        self._driver.switch_to.window(self._driver.window_handles[0])

    # def close_current_window_and_jump_to_origin(self):
    #     self._driver.close()

    #     # jump back to origin window
    #     windows = self._driver.window_handles
    #     assert len(windows) == 1
    #     self._driver.switch_to.window(windows[0])

    def find_container_btn_and_click(self, container_btn_css, container_no):
        container_btn = self._driver.find_element_by_css_selector(container_btn_css)
        container_btn.click()

    def search(self, search_no, search_type):
        try:
            # handle cookies
            cookie_accept_btn = WebDriverWait(self._driver, 20).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "form > button#btn_cookie_accept"))
            )
            cookie_accept_btn.click()
            time.sleep(2)
        except Exception:
            pass

        drop_down_btn = self._driver.find_element_by_css_selector("button[data-id='ooclCargoSelector']")
        drop_down_btn.click()
        if search_type == SEARCH_TYPE_MBL:
            bl_select = self._driver.find_element_by_css_selector("li[data-original-index='0'] > a")
        else:
            bl_select = self._driver.find_element_by_css_selector("li[data-original-index='1'] > a")

        bl_select.click()

        time.sleep(2)
        search_bar = self._driver.find_element_by_css_selector("input#SEARCH_NUMBER")
        search_bar.clear()
        time.sleep(1)
        search_bar.send_keys(search_no)
        time.sleep(2)
        search_btn = self._driver.find_element_by_css_selector("a#container_btn")
        search_btn.click()

    def _is_blocked(self, response):
        res = response.xpath("/html/body/title/text()").extract()
        if res and str(res[0]) == "Error":
            return True
        else:
            return False

    def _handle_with_slide(self, info_pack: Dict):
        max_retry_times = 5
        retry_times = 0

        while True:
            if retry_times > max_retry_times:
                raise MaxRetryError(**info_pack, reason=f"Retry more than {max_retry_times} times")

            if not self._pass_verification_or_not():
                break
            try:
                slider_ele = self._get_slider()
            except TimeoutException:
                break
            icon_ele = self._get_slider_icon_ele()
            img_ele = self._get_bg_img_ele()

            distance = self._get_element_slide_distance(icon_ele, img_ele, 0)

            if distance <= 100:
                self._refresh()
                continue

            track = self._get_track(distance)
            self._move_to_gap(slider_ele, track)

            time.sleep(10)
            retry_times += 1

    def _pass_verification_or_not(self):
        try:
            return self._driver.find_element_by_id("recaptcha_div")
        except NoSuchElementException:
            return None

    def _get_slider(self):
        WebDriverWait(self._driver, 15).until(
            EC.presence_of_element_located(
                (By.XPATH, "/html/body/form[1]/div[4]/div[3]/div[2]/div[1]/div/div[2]/div/div/i")
            )
        )
        return self._driver.find_element_by_xpath("/html/body/form[1]/div[4]/div[3]/div[2]/div[1]/div/div[2]/div/div/i")

    def _get_slider_icon_ele(self):
        canvas = self._driver.find_element_by_xpath('//*[@id="bockCanvas"]')
        canvas_base64 = self._driver.execute_script("return arguments[0].toDataURL('image/png').substring(21);", canvas)
        return canvas_base64

    def _get_bg_img_ele(self):
        canvas = self._driver.find_element_by_xpath('//*[@id="imgCanvas"]')
        canvas_base64 = self._driver.execute_script("return arguments[0].toDataURL('image/png').substring(21);", canvas)
        return canvas_base64

    def _get_element_slide_distance(self, slider_ele, background_ele, correct=0):
        """
        根据传入滑块，和背景的节点，计算滑块的距离
        ​
        该方法只能计算 滑块和背景图都是一张完整图片的场景，
        如果背景图是通过多张小图拼接起来的背景图，
        该方法不适用，请使用get_image_slide_distance这个方法
        :param slider_ele: 滑块图片的节点
        :type slider_ele: WebElement
        :param background_ele: 背景图的节点
        :type background_ele:WebElement
        :param correct:滑块缺口截图的修正值，默认为0,调试截图是否正确的情况下才会用
        :type: int
        :return: 背景图缺口位置的X轴坐标位置（缺口图片左边界位置）
        """

        slider_pic = self._readb64(slider_ele)
        background_pic = self._readb64(background_ele)

        width, height, _ = slider_pic.shape[::-1]
        slider01 = "slider01.jpg"
        background_01 = "background01.jpg"
        cv2.imwrite(background_01, background_pic)
        cv2.imwrite(slider01, slider_pic)
        # 读取另存的滑块图
        slider_pic = cv2.imread(slider01)
        # 进行色彩转换
        slider_pic = cv2.cvtColor(slider_pic, cv2.COLOR_BGR2GRAY)

        # 获取色差的绝对值
        slider_pic = abs(255 - slider_pic)
        # 保存图片
        cv2.imwrite(slider01, slider_pic)
        # 读取滑块
        slider_pic = cv2.imread(slider01)
        # 读取背景图
        background_pic = cv2.imread(background_01)

        # 比较两张图的重叠区域
        result = cv2.matchTemplate(slider_pic, background_pic, cv2.TM_CCOEFF_NORMED)
        # 获取图片的缺口位置
        top, left = np.unravel_index(result.argmax(), result.shape)
        # print("Current notch position:", (left, top, left + width, top + height))

        return left + width + correct

    def _readb64(self, base64_string):
        _imgdata = base64.b64decode(base64_string)
        _image = Image.open(BytesIO(_imgdata))

        return cv2.cvtColor(np.array(_image), cv2.COLOR_RGB2BGR)

    def _refresh(self):
        refresh_button = self._driver.find_element_by_xpath(
            "/html/body/form[1]/div[4]/div[3]/div[2]/div[1]/div/div[1]/div/div/i"
        )
        refresh_button.click()
        time.sleep(5)

    def _get_track(self, distance):
        """
        follow Newton's laws of motion
        ①v=v0+at
        ②s=v0t+(1/2)at²
        ③v²-v0²=2as
        """
        track = []
        current = 0
        # start to slow until 4/5 of total distance
        mid = distance * 4 / 5
        # time period
        t = 0.2
        # initial speed
        v = 50

        while current < distance:
            if current < mid:
                # acceleration
                a = 3
            else:
                # acceleration
                a = -10
            # # initial speed v0
            v0 = v
            # x = v0t + 1/2 * a * t^2
            move = v0 * t + 1 / 2 * a * t * t
            # current speed, v = v0 + at
            v = v0 + a * t
            current += move
            track.append(round(move))

        return track

    def _move_to_gap(self, slider, track):
        ActionChains(self._driver).click_and_hold(slider).perform()

        for x in track:
            ActionChains(self._driver).move_by_offset(xoffset=x, yoffset=0).perform()
        time.sleep(0.5)  # move to the right place and take a break
        ActionChains(self._driver).release().perform()


class OoluLocalCrawler(BaseLocalCrawler):
    code = "OOLU"

    def __init__(self, proxy):
        super().__init__(proxy=proxy)
        self._search_type = ""
        self._search_nos = []
        self.content_getter = ContentGetter(
            proxy_manager=HydraproxyProxyManager(session="oolu", logger=logger), is_headless=False
        )

    def start_crawler(self, task_ids: str, mbl_nos: str, booking_nos: str, container_nos: str):
        task_ids = task_ids.split(",")
        if mbl_nos:
            self._search_nos = mbl_nos.split(",")
            self._search_type = SEARCH_TYPE_MBL
        elif booking_nos:
            self._search_nos = booking_nos.split(",")
            self._search_type = SEARCH_TYPE_BOOKING

        id_mbl_map = {search_no: task_id for task_id, search_no in zip(task_ids, self._search_nos)}
        for search_no, task_id in id_mbl_map.items():
            for item in self.handle_search_no(search_no, task_id):
                yield item

    def handle_search_no(self, search_no, task_id):
        info_pack = {
            "task_id": task_id,
            "search_no": search_no,
            "search_type": self._search_type,
        }
        res = self.content_getter.search_and_return(info_pack=info_pack)
        response = Selector(text=res)

        rule = CargoTrackingRule(content_getter=self.content_getter, search_type=self._search_type)

        while rule.is_no_response(response=response):
            res = self.content_getter.search_again_and_return(info_pack=info_pack)
            response = Selector(text=res)

        if os.path.exists("./background01.jpg"):
            os.remove("./background01.jpg")
        if os.path.exists("./slider01.jpg"):
            os.remove("./slider01.jpg")

        for item in rule.handle_response(response=response, info_pack=info_pack):
            yield item

        windows = self.content_getter.get_window_handles()
        if len(windows) > 1:
            self.content_getter.close()
            self.content_getter.switch_to_first()
