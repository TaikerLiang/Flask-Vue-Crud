import base64
import dataclasses
import logging
import os
import re
import time
from io import BytesIO
from typing import Dict, List, Optional

import cv2
import numpy as np
import scrapy
from PIL import Image
from scrapy import Selector
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from urllib3.exceptions import ReadTimeoutError

from crawler.core.base_new import (
    DUMMY_URL_DICT,
    RESULT_STATUS_ERROR,
    SEARCH_TYPE_BOOKING,
    SEARCH_TYPE_CONTAINER,
    SEARCH_TYPE_MBL,
)
from crawler.core.exceptions_new import (
    AccessDeniedError,
    FormatError,
    MaxRetryError,
    SuspiciousOperationError,
    TimeOutError,
)
from crawler.core.items_new import DataNotFoundItem, EndItem
from crawler.core.proxy_new import HydraproxyProxyManager
from crawler.core.selenium import ChromeContentGetter
from crawler.core.table import BaseTable, TableExtractor
from crawler.core_carrier.base_spiders_new import BaseMultiCarrierSpider
from crawler.core_carrier.items_new import (
    BaseCarrierItem,
    ContainerItem,
    ContainerStatusItem,
    DebugItem,
    LocationItem,
    MblItem,
    VesselItem,
)
from crawler.core_carrier.request_helpers_new import RequestOption
from crawler.core_carrier.rules import BaseRoutingRule, RuleManager
from crawler.extractors.selector_finder import (
    CssQueryTextStartswithMatchRule,
    find_selector_from,
)
from crawler.extractors.table_cell_extractors import (
    BaseTableCellExtractor,
    FirstTextTdExtractor,
)

MAX_RETRY_COUNT = 10
BASE_URL = "http://moc.oocl.com"


@dataclasses.dataclass
class Restart:
    search_nos: list
    task_ids: list
    reason: str = ""


class CarrierOoluSpider(BaseMultiCarrierSpider):
    name = "carrier_oolu_multi"
    custom_settings = {
        **BaseMultiCarrierSpider.custom_settings,  # type: ignore
        "CLOSESPIDER_TIMEOUT": 30 * 60,
        "CONCURRENT_REQUESTS": "1",
    }

    def __init__(self, *args, **kwargs):
        super(CarrierOoluSpider, self).__init__(*args, **kwargs)
        self._retry_count = 0
        self._content_getter = self._make_content_getter()

        bill_rules = [
            CargoTrackingRule(self._content_getter, search_type=SEARCH_TYPE_MBL),
            NextRoundRoutingRule(),
        ]

        booking_rules = [
            CargoTrackingRule(self._content_getter, search_type=SEARCH_TYPE_BOOKING),
            NextRoundRoutingRule(),
        ]

        if self.search_type == SEARCH_TYPE_MBL:
            self._rule_manager = RuleManager(rules=bill_rules)
        elif self.search_type == SEARCH_TYPE_BOOKING:
            self._rule_manager = RuleManager(rules=booking_rules)

    def start(self):
        option = CargoTrackingRule.build_request_option(search_nos=self.search_nos, task_ids=self.task_ids)
        yield self._build_request_by(option=option)

    def parse(self, response):
        yield DebugItem(info={"meta": dict(response.meta)})

        routing_rule = self._rule_manager.get_rule_by_response(response=response)

        save_name = routing_rule.get_save_name(response=response)
        self._saver.save(to=save_name, text=response.text)

        for result in routing_rule.handle(response=response):
            if isinstance(result, (BaseCarrierItem, DataNotFoundItem, EndItem)):
                yield result
            elif isinstance(result, Restart):
                yield DebugItem(info=f"{result.reason}, Restart {self._retry_count + 1} times ...")
                option = self._prepare_restart(search_nos=result.search_nos, task_ids=result.task_ids)
                yield self._build_request_by(option=option)
            elif isinstance(result, RequestOption):
                yield self._build_request_by(option=result)
            else:
                raise RuntimeError()

    def _prepare_restart(self, search_nos: List, task_ids: List):
        if self._retry_count >= MAX_RETRY_COUNT:
            raise MaxRetryError(
                task_id=task_ids[0],
                search_no=search_nos[0],
                search_type=self.search_type,
                reason=f"Retry more than {MAX_RETRY_COUNT} times",
            )

        self._retry_count += 1
        self._content_getter.quit()
        time.sleep(3)

        self._content_getter = self._make_content_getter()
        self._rule_manager.get_rule_by_name(CargoTrackingRule.name).set_content_getter(self._content_getter)
        return CargoTrackingRule.build_request_option(search_nos=search_nos, task_ids=task_ids)

    def _make_content_getter(self):
        return ContentGetter(proxy_manager=HydraproxyProxyManager(session="oolu", logger=self.logger), is_headless=True)

    def _build_request_by(self, option: RequestOption):
        meta = {
            RuleManager.META_CARRIER_CORE_RULE_NAME: option.rule_name,
            **option.meta,
        }

        if option.method == RequestOption.METHOD_GET:
            return scrapy.Request(
                url=option.url,
                headers=option.headers,
                meta=meta,
                dont_filter=True,
                callback=self.parse,
            )

        else:
            zip_list = list(zip(meta["task_ids"], meta["search_nos"]))
            raise SuspiciousOperationError(
                task_id=meta["task_ids"][0],
                search_type=self.search_type,
                reason=f"Unexpected request method: `{option.method}`, on (task_id, search_no): {zip_list}",
            )


class ContentGetter(ChromeContentGetter):
    MAX_SEARCH_TIMES = 10

    def __init__(self, proxy_manager, is_headless):
        super().__init__(proxy_manager=proxy_manager, is_headless=is_headless)

        logging.getLogger("seleniumwire").setLevel(logging.ERROR)
        logging.getLogger("hpack").setLevel(logging.INFO)

        self._driver.set_page_load_timeout(120)

        self._search_count = 0

    def goto(self):
        self._driver.get("https://www.oocl.com/eng/ourservices/eservices/cargotracking/Pages/cargotracking.aspx")
        time.sleep(3)

    def search_and_return(self, info_pack: Dict):
        search_no = info_pack["search_no"]
        search_type = info_pack["search_type"]

        self._search(search_no=search_no, search_type=search_type)
        time.sleep(7)
        windows = self._driver.window_handles
        self._driver.switch_to.window(windows[1])  # windows[1] is new page
        WebDriverWait(self._driver, 120).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div#recaptcha_div")))
        if self._is_blocked(response=Selector(text=self._driver.page_source)):
            raise AccessDeniedError(**info_pack, reason="Blocked during searching")

        if self._is_first:
            self._is_first = False
        self._handle_with_slide(info_pack=info_pack)
        time.sleep(10)

        self._search_count = 0
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

        self._driver.refresh()
        time.sleep(3)
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

    def find_container_btn_and_click(self, container_btn_css):
        container_btn = self._driver.find_element_by_css_selector(container_btn_css)
        container_btn.click()

    def _search(self, search_no, search_type):
        if self._is_first:
            # handle cookies
            cookie_accept_btn = WebDriverWait(self._driver, 20).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "form > button#btn_cookie_accept"))
            )
            cookie_accept_btn.click()
            time.sleep(2)

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

            distance = self._get_element_slide_distance(icon_ele, img_ele, 1)

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


# -------------------------------------------------------------------------------


class CargoTrackingRule(BaseRoutingRule):
    name = "CARGO_TRACKING"

    def __init__(self, content_getter: ContentGetter, search_type):
        self._content_getter = content_getter
        self._search_type = search_type

    @classmethod
    def build_request_option(cls, search_nos, task_ids) -> RequestOption:
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=DUMMY_URL_DICT["eval_edi"],
            meta={
                "search_nos": search_nos,
                "task_ids": task_ids,
            },
        )

    def get_save_name(self, response) -> str:
        return f"{self.name}.html"

    def set_content_getter(self, content_getter: ContentGetter):
        self._content_getter = content_getter

    def handle(self, response):
        search_nos = response.meta["search_nos"]
        task_ids = response.meta["task_ids"]
        info_pack = {
            "task_id": task_ids[0],
            "search_no": search_nos[0],
            "search_type": self._search_type,
        }

        try:
            self._content_getter.goto()
            windows = self._content_getter.get_window_handles()
            if len(windows) > 1:
                self._content_getter.close()
                self._content_getter.switch_to_first()

            res = self._content_getter.search_and_return(info_pack=info_pack)
            response = Selector(text=res)

            while self._no_response(response=response):
                res = self._content_getter.search_again_and_return(info_pack=info_pack)
                response = Selector(text=res)
        except Exception as e:
            yield Restart(search_nos=search_nos, task_ids=task_ids, reason=repr(e))
            return

        if os.path.exists("./background01.jpg"):
            os.remove("./background01.jpg")
        if os.path.exists("./slider01.jpg"):
            os.remove("./slider01.jpg")

        for item in self._handle_response(response=response, info_pack=info_pack):
            yield item

        yield NextRoundRoutingRule.build_request_option(search_nos=search_nos, task_ids=task_ids)

    def _no_response(self, response: Selector) -> bool:
        return not bool(response.css("td.pageTitle"))

    def _handle_response(self, response, info_pack: Dict):
        if self.is_search_no_invalid(response):
            yield DataNotFoundItem(**info_pack, status=RESULT_STATUS_ERROR, detail="Data was not found")
            return

        task_id = info_pack["task_id"]
        search_no = info_pack["search_no"]
        search_type = info_pack["search_type"]

        locator = _PageLocator(info_pack=info_pack)
        selector_map = locator.locate_selectors(response=response)

        custom_release_info = self._extract_custom_release_info(selector_map=selector_map, info_pack=info_pack)
        routing_info, vessel_list = self._extract_routing_info(selectors_map=selector_map, info_pack=info_pack)
        for vessel in vessel_list:
            yield VesselItem(
                task_id=task_id,
                vessel_key=vessel["vessel"] or None,
                vessel=vessel["vessel"] or None,
                voyage=vessel["voyage"] or None,
                pol=LocationItem(name=vessel["pol"] or None),
                pod=LocationItem(name=vessel["pod"] or None),
                etd=vessel["etd"] or None,
                atd=vessel["atd"] or None,
                eta=vessel["eta"] or None,
                ata=vessel["ata"] or None,
            )

        mbl_item = MblItem(
            task_id=task_id,
            vessel=routing_info["vessel"] or None,
            voyage=routing_info["voyage"] or None,
            por=LocationItem(name=routing_info["por"] or None),
            pol=LocationItem(name=routing_info["pol"] or None),
            pod=LocationItem(name=routing_info["pod"] or None),
            etd=routing_info["etd"] or None,
            atd=routing_info["atd"] or None,
            eta=routing_info["eta"] or None,
            ata=routing_info["ata"] or None,
            place_of_deliv=LocationItem(name=routing_info["place_of_deliv"] or None),
            deliv_eta=routing_info["deliv_eta"] or None,
            deliv_ata=routing_info["deliv_ata"] or None,
            final_dest=LocationItem(name=routing_info["final_dest"] or None),
            customs_release_status=custom_release_info["status"] or None,
            customs_release_date=custom_release_info["date"] or None,
        )

        if search_type == SEARCH_TYPE_MBL:
            mbl_item["mbl_no"] = search_no
        else:
            mbl_item["booking_no"] = search_no
        yield mbl_item

        container_list = self._extract_container_list(selector_map=selector_map)
        for i, container in enumerate(container_list):
            container_no = container["container_no"].strip()
            click_element_css = f"a[id='form:link{i}']"

            try:
                self._content_getter.find_container_btn_and_click(container_btn_css=click_element_css)
                time.sleep(10)
            except ReadTimeoutError:
                url = self._content_getter.get_current_url()
                self._content_getter.quit()
                raise TimeOutError(
                    **info_pack,
                    reason=f"Timeout during connect to {url}",
                )

            response = Selector(text=self._content_getter.get_page_source())

            for item in self._handle_container_response(
                response=response,
                task_id=task_id,
                container_no=container_no,
                terminal_pod=routing_info["teminal_pod"],
                terminal_final_dest=routing_info["terminal_final_dest"],
            ):
                yield item

        yield EndItem(task_id=task_id)

    def is_search_no_invalid(self, response):
        if response.css("span[class=noRecordBold]"):
            return True
        return False

    def _extract_custom_release_info(self, selector_map: Dict[str, scrapy.Selector], info_pack: Dict):
        table = selector_map["summary:main_right_table"]

        table_locator = SummaryRightTableLocator()
        table_locator.parse(table)
        table_extractor = TableExtractor(table_locator)
        first_td_extractor = FirstTextTdExtractor()

        if not table_extractor.has_header(left="Inbound Customs Clearance Status:"):
            return {
                "status": "",
                "date": "",
            }

        custom_release_info = table_extractor.extract_cell(
            left="Inbound Customs Clearance Status:", extractor=first_td_extractor
        )
        custom_release_status, custom_release_date = self._parse_custom_release_info(
            custom_release_info=custom_release_info, info_pack=info_pack
        )

        return {
            "status": custom_release_status.strip(),
            "date": custom_release_date.strip(),
        }

    def _parse_custom_release_info(self, custom_release_info: str, info_pack: Dict):
        """
        Sample 1: `Cleared (03 Nov 2019, 16:50 GMT)`
        Sample 2: `Not Applicable`
        Sample 3: ``
        """
        if not custom_release_info:
            return "", ""

        pattern = re.compile(r"^(?P<status>[^(]+)(\s+[(](?P<date>[^)]+)[)])?$")
        match = pattern.match(custom_release_info)
        if not match:
            raise FormatError(
                **info_pack,
                reason=f"Unknown custom_release_info: `{custom_release_info}`",
            )
        return match.group("status").strip(), match.group("date") or ""

    def _extract_routing_info(self, selectors_map: Dict[str, scrapy.Selector], info_pack: Dict):
        table = selectors_map.get("detail:routing_table", None)
        if table is None:
            return {
                "por": "",
                "pol": "",
                "pod": "",
                "place_of_deliv": "",
                "final_dest": "",
                "etd": "",
                "atd": "",
                "eta": "",
                "ata": "",
                "deliv_eta": "",
                "deliv_ata": "",
                "vessel": "",
                "voyage": "",
            }, []

        table_locator = RoutingTableLocator()
        table_locator.parse(table=table)
        table_extractor = TableExtractor(table_locator=table_locator)
        span_extractor = FirstTextTdExtractor("span::text")

        vessel_voyage_extractor = VesselVoyageTdExtractor(info_pack=info_pack)
        vessel_list = []
        for left in table_locator.iter_left_header():
            vessel_voyage = table_extractor.extract_cell(
                top="Vessel Voyage", left=left, extractor=vessel_voyage_extractor
            )

            # pol / pod
            pol_pod_extractor = PolPodTdExtractor(info_pack=info_pack)

            pol_info = table_extractor.extract_cell(top="Port of Load", left=left, extractor=pol_pod_extractor)
            etd, atd = self._get_est_and_actual(
                status=pol_info["status"], time_str=pol_info["time_str"], info_pack=info_pack
            )

            pod_info = table_extractor.extract_cell(top="Port of Discharge", left=left, extractor=pol_pod_extractor)
            eta, ata = self._get_est_and_actual(
                status=pod_info["status"], time_str=pod_info["time_str"], info_pack=info_pack
            )

            vessel_list.append(
                {
                    "pol": pol_info["port"],
                    "pod": pod_info["port"],
                    "etd": etd,
                    "atd": atd,
                    "eta": eta,
                    "ata": ata,
                    "vessel": vessel_voyage["vessel"],
                    "voyage": vessel_voyage["voyage"],
                }
            )

        # vessel_voyage
        vessel_voyage = table_extractor.extract_cell(
            top="Vessel Voyage", left=table_locator.LAST_LEFT_HEADER, extractor=vessel_voyage_extractor
        )

        # por
        por = table_extractor.extract_cell(top="Origin", left=table_locator.FIRST_LEFT_HEADER, extractor=span_extractor)

        # pol / pod
        pol_pod_extractor = PolPodTdExtractor(info_pack=info_pack)

        pol_info = table_extractor.extract_cell(
            top="Port of Load", left=table_locator.FIRST_LEFT_HEADER, extractor=pol_pod_extractor
        )
        etd, atd = self._get_est_and_actual(
            status=pol_info["status"], time_str=pol_info["time_str"], info_pack=info_pack
        )

        pod_info = table_extractor.extract_cell(
            top="Port of Discharge", left=table_locator.LAST_LEFT_HEADER, extractor=pol_pod_extractor
        )
        eta, ata = self._get_est_and_actual(
            status=pod_info["status"], time_str=pod_info["time_str"], info_pack=info_pack
        )

        # place_of_deliv
        deliv_extractor = DelivTdExtractor(info_pack=info_pack)
        deliv_info = table_extractor.extract_cell(
            top="Final Destination Hub", left=table_locator.LAST_LEFT_HEADER, extractor=deliv_extractor
        )
        deliv_eta, deliv_ata = self._get_est_and_actual(
            status=deliv_info["status"], time_str=deliv_info["time_str"], info_pack=info_pack
        )

        # final_dest
        final_dest = table_extractor.extract_cell(
            top="Destination", left=table_locator.LAST_LEFT_HEADER, extractor=span_extractor
        )

        if pod_info["port"] == final_dest:
            terminal_pod = deliv_info["port"]
            terminal_final_dest = None
        else:
            terminal_pod = None
            terminal_final_dest = deliv_info["port"]

        routing_info = {
            "por": por,
            "pol": pol_info["port"],
            "pod": pod_info["port"],
            "place_of_deliv": deliv_info["port"],
            "final_dest": final_dest,
            "terminal_pod": terminal_pod,
            "terminal_final_dest": terminal_final_dest,
            "etd": etd,
            "atd": atd,
            "eta": eta,
            "ata": ata,
            "deliv_eta": deliv_eta,
            "deliv_ata": deliv_ata,
            "vessel": vessel_voyage["vessel"],
            "voyage": vessel_voyage["voyage"],
        }

        return routing_info, vessel_list

    def _extract_container_list(self, selector_map: Dict[str, scrapy.Selector]):
        table = selector_map["summary:container_table"]

        container_table_locator = ContainerTableLocator()
        container_table_locator.parse(table=table)
        table_extractor = TableExtractor(table_locator=container_table_locator)

        container_no_list = []
        for left in container_table_locator.iter_left_header():
            container_no_text = table_extractor.extract_cell("Container Number", left)
            # container_no_text: OOLU843521-8
            container_id, check_no = container_no_text.split("-")
            container_no_list.append(
                {
                    "container_id": container_id,
                    "container_no": f"{container_id}{check_no}",
                }
            )
        return container_no_list

    def _handle_container_response(
        self, response, task_id: str, container_no: str, terminal_pod: Optional[str], terminal_final_dest: Optional[str]
    ):
        info_pack = {
            "task_id": task_id,
            "search_no": container_no,
            "search_type": SEARCH_TYPE_CONTAINER,
        }

        title_container_no = self._extract_container_no(response, info_pack=info_pack)
        if title_container_no != info_pack["search_no"]:
            raise FormatError(
                **info_pack,
                reason=f"Container no mismatch: website={title_container_no}, ours={info_pack['search_no']}",
            )

        locator = _PageLocator(info_pack=info_pack)
        selectors_map = locator.locate_selectors(response=response)
        detention_info = self._extract_detention_info(selectors_map, info_pack=info_pack)

        yield ContainerItem(
            task_id=info_pack["task_id"],
            container_key=info_pack["search_no"],
            container_no=info_pack["search_no"],
            last_free_day=detention_info["last_free_day"] or None,
            det_free_time_exp_date=detention_info["det_free_time_exp_date"] or None,
            terminal_pod=LocationItem(name=terminal_pod),
            terminal_final_dest=LocationItem(name=terminal_final_dest),
        )

        container_status_list = self._extract_container_status_list(selectors_map)
        for container_status in container_status_list:
            event = container_status["event"].strip()
            facility = container_status["facility"]

            if facility:
                description = f"{event} ({facility})"
            else:
                description = event

            yield ContainerStatusItem(
                task_id=info_pack["task_id"],
                container_key=info_pack["search_no"],
                description=description,
                location=LocationItem(name=container_status["location"]),
                transport=container_status["transport"],
                local_date_time=container_status["local_date_time"],
            )

    def _extract_search_no(self, response, info_pack: Dict):
        search_no_text = response.css("th.sectionTable::text").get()
        search_no = self._parse_search_no_text(search_no_text=search_no_text, info_pack=info_pack)
        return search_no

    def _parse_search_no_text(self, search_no_text: str, info_pack: Dict):
        # Search Result - Bill of Lading Number  2109051600
        # Search Result - Booking Number  2636035340
        pattern = re.compile(r"^Search\s+Result\s+-\s+(Bill\s+of\s+Lading|Booking)\s+Number\s+(?P<search_no>\d+)\s+$")
        match = pattern.match(search_no_text)
        if not match:
            raise FormatError(
                **info_pack,
                reason=f"Unknown search_no_text: `{search_no_text}`",
            )

        return match.group("search_no")

    def _extract_container_no(self, response: Selector, info_pack: Dict):
        container_no_text = response.css("td.groupTitle.fullByDraftCntNumber::text").get()
        pattern = re.compile(r"^Detail\s+of\s+OOCL\s+Container\s+(?P<container_id>\w+)-(?P<check_no>\d+)\s+$")
        match = pattern.match(container_no_text)
        if not match:
            raise FormatError(
                **info_pack,
                reason=f"Unknown container_no_text: `{container_no_text}`",
            )

        return match.group("container_id") + match.group("check_no")

    def _extract_detention_info(self, selectors_map: Dict[str, scrapy.Selector], info_pack: Dict):
        table = selectors_map.get("detail:detention_right_table", None)
        if table is None:
            return {
                "last_free_day": "",
                "det_free_time_exp_date": "",
            }

        table_locator = DestinationTableLocator()
        table_locator.parse(table=table)
        table_extractor = TableExtractor(table_locator=table_locator)
        td_extractor = DetentionDateTdExtractor(info_pack=info_pack)

        if table_locator.has_header(left="Demurrage Last Free Date:"):
            lfd_info = table_extractor.extract_cell(left="Demurrage Last Free Date:", extractor=td_extractor)
            _, lfd = self._get_est_and_actual(
                status=lfd_info["status"], time_str=lfd_info["time_str"], info_pack=info_pack
            )
        else:
            lfd = ""

        if table_locator.has_header(left="Detention Last Free Date:"):
            det_lfd_info = table_extractor.extract_cell(left="Detention Last Free Date:", extractor=td_extractor)
            _, det_lfd = self._get_est_and_actual(
                status=det_lfd_info["status"], time_str=det_lfd_info["time_str"], info_pack=info_pack
            )
        else:
            det_lfd = ""

        return {
            "last_free_day": lfd,
            "det_free_time_exp_date": det_lfd,
        }

    def _extract_container_status_list(self, selectors_map: Dict[str, scrapy.Selector]):
        table = selectors_map.get("detail:container_status_table", None)
        if table is None:
            return []

        table_locator = ContainerStatusTableLocator()
        table_locator.parse(table=table)
        table_extractor = TableExtractor(table_locator=table_locator)
        first_text_extractor = FirstTextTdExtractor()
        span_extractor = FirstTextTdExtractor(css_query="span::text")

        container_status_list = []
        for left in table_locator.iter_left_header():
            container_status_list.append(
                {
                    "event": table_extractor.extract_cell(top="Event", left=left, extractor=first_text_extractor),
                    "facility": table_extractor.extract_cell(top="Facility", left=left, extractor=first_text_extractor),
                    "location": table_extractor.extract_cell(top="Location", left=left, extractor=span_extractor),
                    "transport": table_extractor.extract_cell(top="Mode", left=left, extractor=first_text_extractor)
                    or None,
                    "local_date_time": table_extractor.extract_cell(top="Time", left=left, extractor=span_extractor),
                }
            )
        return container_status_list

    def _get_est_and_actual(self, status, time_str, info_pack: Dict):
        if status == "(Actual)":
            estimate, actual = None, time_str
        elif status == "(Estimated)":
            estimate, actual = time_str, ""
        elif status == "":
            estimate, actual = None, ""
        else:
            raise FormatError(
                **info_pack,
                reason=f"Unknown status format: `{status}`",
            )

        return estimate, actual


class NextRoundRoutingRule(BaseRoutingRule):
    name = "NEXT_ROUND"

    @classmethod
    def build_request_option(cls, search_nos: List, task_ids: List) -> RequestOption:
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=DUMMY_URL_DICT["eval_edi"],
            meta={
                "search_nos": search_nos,
                "task_ids": task_ids,
            },
        )

    def handle(self, response):
        task_ids = response.meta["task_ids"]
        search_nos = response.meta["search_nos"]

        if len(search_nos) == 1 and len(task_ids) == 1:
            return

        task_ids = task_ids[1:]
        search_nos = search_nos[1:]

        yield CargoTrackingRule.build_request_option(search_nos=search_nos, task_ids=task_ids)


class SummaryRightTableLocator(BaseTable):
    TD_TITLE_INDEX = 0
    TD_DATA_INDEX = 1

    def parse(self, table: Selector):
        tr_list = table.css("tr")

        for tr in tr_list:
            td_list = tr.css("td")
            if not td_list or len(td_list) != 2:
                continue

            title_td = td_list[self.TD_TITLE_INDEX]
            data_td = td_list[self.TD_DATA_INDEX]

            title_not_strip = title_td.css("::text").get()
            title = title_not_strip.strip() if isinstance(title_not_strip, str) else ""
            self.add_left_header_set(title)
            td_dict = self._td_map.setdefault(0, {})
            td_dict[title] = data_td


class RoutingTableLocator(BaseTable):
    """
    +-------------------------------------+ <tbody>
    | Title 1  | Title 2  | ... |   <th>  | <tr>
    +----------+----------+-----+---------+
    | Data 1-1 | Data 2-1 |     |   <td>  | <tr>
    +----------+----------+-----+---------+
    | Data 1-2 | Data 2-2 |     |   <td>  | <tr>
    +----------+----------+-----+---------+
    | ...      | ...      |     |   <td>  | <tr>
    +----------+----------+-----+---------+ </tbody>
    """

    TR_TITLE_INDEX = 0
    TR_DATA_START_INDEX = 1

    FIRST_LEFT_HEADER = 0
    LAST_LEFT_HEADER = -1

    def parse(self, table: scrapy.Selector):
        title_tr = table.css("tr")[self.TR_TITLE_INDEX]
        data_trs = table.css("tr")[self.TR_DATA_START_INDEX :]
        self._left_header_set = set(range(len(data_trs)))

        raw_title_list = title_tr.css("th::text").getall()
        title_list = [title.strip() for title in raw_title_list if isinstance(title, str)]

        for title_index, title in enumerate(title_list):
            data_index = title_index

            self._td_map[title] = []
            for data_tr in data_trs:
                data_td = data_tr.css("td")[data_index]
                self._td_map[title].append(data_td)


class ContainerTableLocator(BaseTable):
    """
    +---------+---------+-----+-------------------------+-----+ <tbody>  -----+
    | Title 1 | Title 2 | ... |      Latest Event       | ... | <tr> <th>     |
    +---------+---------+-----+-------------------------+-----+               |
    |         |         |     | Event | Location | Time |     | <tr> <th>     |
    +---------+---------+-----+-------------------------+-----+               |
    | Data 1  | Data 2  | ... | Data  |   Data   | Data | ... | <tr> <td>     |
    +---------+---------+-----+-------------------------+-----+ <\tbody> -----+
    """

    TR_MAIN_TITLE_INDEX = 0
    TR_SUB_TITLE_INDEX = 1
    TR_DATA_START_INDEX = 2

    def parse(self, table: scrapy.Selector):
        tr_list = table.xpath("./tr") or table.xpath("./tbody/tr")

        main_title_list = tr_list[self.TR_MAIN_TITLE_INDEX].css("th::text").getall()
        sub_title_list = tr_list[self.TR_SUB_TITLE_INDEX].css("th::text").getall()
        data_tr_list = tr_list[self.TR_DATA_START_INDEX :]
        self._left_header_set = set(range(len(data_tr_list)))

        title_list = []
        for main_title_index, main_title in enumerate(main_title_list):
            main_title = main_title.strip() if isinstance(main_title, str) else ""

            if main_title == "Latest Event":
                sub_title_list = [sub.strip() for sub in sub_title_list if isinstance(sub, str)]
                title_list.extend(sub_title_list)
            else:
                title_list.append(main_title)

        for title_index, title in enumerate(title_list):
            data_index = title_index

            self._td_map[title] = []
            for data_tr in data_tr_list:
                data_td = data_tr.css("td")[data_index]
                self._td_map[title].append(data_td)


class VesselVoyageTdExtractor(BaseTableCellExtractor):
    def __init__(self, info_pack: Dict) -> None:
        super().__init__()
        self._info_pack = info_pack

    def extract(self, cell: Selector):
        text_list = cell.css("::text").getall()

        if len(text_list) != 2:
            FormatError(
                **self._info_pack,
                reason=f"Unknown Vessel Voyage td format: `{text_list}`",
            )

        if text_list[0].strip() == "":
            return {
                "vessel": "",
                "voyage": "",
            }

        vessel = self._parse_vessel(text_list[0])

        return {
            "vessel": vessel,
            "voyage": text_list[1].strip(),
        }

    def _parse_vessel(self, text):
        """
        Sample 1:
            text = (
                '\n'
                '\t\t\t\t\t\t\t\t\t\t\t\t\t\t  ECC2\n'
                '\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t  EVER LEADER\xa0\n'
                '\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t  '
            )
            result = 'EVER LEADER'

        Sample 2:
            text = (
                '\n'
                '\t\t\t\t\t\t\t\t\t\t\t\t\t\t  SC2\n'
                '\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t  XIN YING KOU\xa0\n'
                '\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t  '
            )
            result = 'XIN YING KOU'
        """
        lines = text.strip().split("\n")

        vessel = lines[1].strip()
        return vessel


class PolPodTdExtractor(BaseTableCellExtractor):
    def __init__(self, info_pack: Dict) -> None:
        super().__init__()
        self._info_pack = info_pack

    def extract(self, cell: Selector):
        text_list = cell.css("::text").getall()

        if len(text_list) < 4:
            raise FormatError(
                **self._info_pack,
                reason=f"Unknown Pol or Pod td format: `{text_list}`",
            )

        return {
            "port": text_list[0].strip(),
            "time_str": text_list[2].strip(),
            "status": text_list[3].strip(),
        }


class DelivTdExtractor(BaseTableCellExtractor):
    def __init__(self, info_pack: Dict) -> None:
        super().__init__()
        self._info_pack = info_pack

    def extract(self, cell: Selector):
        text_list = cell.css("::text").getall()

        if len(text_list) < 3:
            raise FormatError(
                **self._info_pack,
                reason=f"Unknown Deliv td format: `{text_list}`",
            )

        return {
            "port": text_list[0].strip(),
            "time_str": text_list[1].strip(),
            "status": text_list[2].strip(),
        }


class ContainerStatusTableLocator(BaseTable):
    """
    +--------------------------------------+ <tbody>
    | Title 1  | Title 2  | ... | Title N  | <tr> <th>
    +----------+----------+-----+----------+
    | Data 1,1 | Data 2,1 | ... | Data N,1 | <tr> <td>
    +----------+----------+-----+----------+
    | Data 1,2 | Data 2,2 | ... | Data N,2 | <tr> <td>
    +----------+----------+-----+----------+
    | ...      | ...      | ... | ...      | <tr> <td>
    +----------+----------+-----+----------+
    | Data 1,M | Data 2,M | ... | Data N,M | <tr> <td>
    +----------+----------+-----+----------+ </tbody>
    """

    DATA_START_TR_INDEX = 1

    def parse(self, table: scrapy.Selector):
        title_list = table.css("th::text").getall()
        data_tr_list = table.css("tr")[self.DATA_START_TR_INDEX :]
        self._left_header_set = set(range(len(data_tr_list)))

        for title_index, title in enumerate(title_list):
            data_index = title_index

            title = title.strip()
            self._td_map[title] = []
            for data_tr in data_tr_list:
                data_td = data_tr.css("td")[data_index]
                self._td_map[title].append(data_td)


class DestinationTableLocator(BaseTable):
    """
    +--------------------------------+ <tbody>
    | Title 1 | Data 1,1  | Data 1,2 | <tr> <td>
    +---------+-----------+----------+
    | Title 2 | Data 2,1  | Data 2,2 | <tr> <td>
    +---------+-----------+----------+
    | Title 3 | Data 3,1  | Data 3,2 | <tr> <td>
    +---------+-----------+----------+
    | ...     |           |          | <tr> <td>
    +---------+-----------+----------+
    | Title N | Data N,1  | Data N,2 | <tr> <td>
    +---------+-----------+----------+ </tbody>
    """

    TITLE_TD_INDEX = 0
    DATA_NEEDED_TD_INDEX = 2

    def parse(self, table: scrapy.Selector):
        tr_list = table.css("tr")

        for tr in tr_list:
            td_list = tr.css("td")

            title_td = td_list[self.TITLE_TD_INDEX]
            title = title_td.css("::text").get()
            title = title.strip() if isinstance(title, str) else ""
            self.add_left_header_set(title)
            td_dict = self._td_map.setdefault(0, {})
            td_dict[title] = td_list[self.DATA_NEEDED_TD_INDEX]


class DetentionDateTdExtractor(BaseTableCellExtractor):
    def __init__(self, info_pack: Dict) -> None:
        super().__init__()
        self._info_pack = info_pack

    def extract(self, cell: Selector):
        text_list = cell.css("::text").getall()
        text_list_len = len(text_list)

        if text_list_len != 2 or text_list_len != 1:
            FormatError(
                **self._info_pack,
                reason=f"Unknown last free day td format: `{text_list}`",
            )

        return {
            "time_str": text_list[0].strip(),
            "status": text_list[1].strip() if text_list_len == 2 else "",
        }


# -------------------------------------------------------------------------------


class _PageLocator:
    def __init__(self, info_pack: Dict) -> None:
        self._info_pack = info_pack

    def locate_selectors(self, response: scrapy.Selector):
        tables = response.css("table.groupTable")

        # summary
        summary_rule = CssQueryTextStartswithMatchRule(css_query="td.groupTitle::text", startswith="Summary")
        summary_table = find_selector_from(selectors=tables, rule=summary_rule)
        if not summary_table:
            raise FormatError(
                **self._info_pack,
                reason="Can not find summary table !!!",
            )
        summary_selectors_map = self._locate_selectors_from_summary(summary_table=summary_table)

        # detail (may not exist)
        detail_rule = CssQueryTextStartswithMatchRule(
            css_query="td.groupTitle::text", startswith="Detail of OOCL Container"
        )
        detail_table = find_selector_from(selectors=tables, rule=detail_rule)
        if detail_table:
            detail_selectors_map = self._locate_selectors_from_detail(detail_table=detail_table)
        else:
            detail_selectors_map = {}

        return {
            **summary_selectors_map,
            **detail_selectors_map,
        }

    def _locate_selectors_from_summary(self, summary_table: scrapy.Selector):
        # top table
        top_table = summary_table.xpath("./tr/td/table") or summary_table.xpath("./tbody/tr/td/table")
        if not top_table:
            raise FormatError(
                **self._info_pack,
                reason="Can not find top_table !!!",
            )

        top_inner_tables = top_table.xpath("./tr/td") or top_table.xpath("./tbody/tr/td")
        if len(top_inner_tables) != 2:
            raise FormatError(
                **self._info_pack,
                reason=f"Amount of top_inner_tables not right: `{len(top_inner_tables)}`",
            )

        # bottom table
        bottom_table = summary_table.css("div#summaryDiv > table")
        if not bottom_table:
            raise FormatError(
                **self._info_pack,
                reason="Can not find container_outer_table !!!",
            )

        bottom_inner_tables = bottom_table.css("tr table")
        if not bottom_inner_tables:
            raise FormatError(
                **self._info_pack,
                reason="Can not find container_inner_table !!!",
            )

        return {
            "summary:main_left_table": top_inner_tables[0],
            "summary:main_right_table": top_inner_tables[1],
            "summary:container_table": bottom_inner_tables[0],
        }

    def _locate_selectors_from_detail(self, detail_table: scrapy.Selector):
        # routing tab
        routing_tab = detail_table.css("div#Tab1")
        if not routing_tab:
            raise FormatError(
                **self._info_pack,
                reason="Can not find routing_tab !!!",
            )

        routing_table = routing_tab.css("table#eventListTable")
        if not routing_table:
            raise FormatError(
                **self._info_pack,
                reason="Can not find routing_table !!!",
            )

        # equipment tab
        equipment_tab = detail_table.css("div#Tab2")
        if not equipment_tab:
            raise FormatError(
                **self._info_pack,
                reason="Can not find equipment_tab !!!",
            )

        equipment_table = equipment_tab.css("table#eventListTable")
        if not equipment_table:
            raise FormatError(
                **self._info_pack,
                reason="Can not find equipment_table !!!",
            )

        # detention tab
        detention_tab = detail_table.css("div#Tab3")
        if not detention_tab:
            raise FormatError(
                **self._info_pack,
                reason="Can not find detention_tab !!!",
            )

        detention_tables = self._locate_detail_detention_tables(detention_tab=detention_tab)

        return {
            "detail:routing_table": routing_table,
            "detail:container_status_table": equipment_table,
            "detail:detention_right_table": detention_tables[1],
        }

    def _locate_detail_detention_tables(self, detention_tab: scrapy.Selector):
        inner_parts = detention_tab.xpath("./table/tr/td/table") or detention_tab.xpath("./table/tbody/tr/td/table")
        if len(inner_parts) != 2:
            raise FormatError(
                **self._info_pack,
                reason=f"Amount of detention_inner_parts not right: `{len(inner_parts)}`",
            )

        title_part, content_part = inner_parts

        detention_tables = content_part.xpath("./tr/td/table/tr/td/table") or content_part.xpath(
            "./tbody/tr/td/table/tbody/tr/td/table"
        )
        if len(detention_tables) != 2:
            raise FormatError(
                **self._info_pack, reason=f"Amount of detention tables does not right: {len(detention_tables)}"
            )

        return detention_tables


# def get_multipart_body(form_data, boundary):
#     body = ""
#     for index, key in enumerate(form_data):
#         body += f"--{boundary}\r\n" f'Content-Disposition: form-data; name="{key}"\r\n' f"\r\n" f"{form_data[key]}\r\n"
#     body += f"--{boundary}--"
#     return body
