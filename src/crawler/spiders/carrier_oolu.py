import os
import re
import time
import base64
from typing import Dict
from io import BytesIO

import scrapy
import cv2
import numpy as np
from scrapy import Selector
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.wait import WebDriverWait
from urllib3.exceptions import ReadTimeoutError
from PIL import Image

from crawler.core.selenium import ChromeContentGetter
from crawler.core_carrier.base import SHIPMENT_TYPE_MBL, SHIPMENT_TYPE_BOOKING
from crawler.core_carrier.base_spiders import BaseCarrierSpider
from crawler.core.proxy import HydraproxyProxyManager
from crawler.core_carrier.request_helpers import RequestOption
from crawler.core_carrier.rules import RuleManager, BaseRoutingRule
from crawler.core_carrier.items import (
    BaseCarrierItem,
    MblItem,
    LocationItem,
    ContainerItem,
    ContainerStatusItem,
    DebugItem,
)
from crawler.core_carrier.exceptions import (
    CarrierResponseFormatError,
    CarrierInvalidMblNoError,
    LoadWebsiteTimeOutError,
    CarrierInvalidSearchNoError,
)
from crawler.extractors.selector_finder import CssQueryTextStartswithMatchRule, find_selector_from
from crawler.extractors.table_extractors import BaseTableLocator, HeaderMismatchError, TableExtractor
from crawler.extractors.table_cell_extractors import BaseTableCellExtractor, FirstTextTdExtractor


BASE_URL = "http://moc.oocl.com"


class CarrierOoluSpider(BaseCarrierSpider):
    name = "carrier_oolu"

    def __init__(self, *args, **kwargs):
        super(CarrierOoluSpider, self).__init__(*args, **kwargs)
        self._content_getter = ContentGetter()

        bill_rules = [
            CargoTrackingRule(self._content_getter, search_type=SHIPMENT_TYPE_MBL),
            ContainerStatusRule(self._content_getter),
        ]

        booking_rules = [
            CargoTrackingRule(self._content_getter, search_type=SHIPMENT_TYPE_BOOKING),
            ContainerStatusRule(self._content_getter),
        ]

        if self.mbl_no:
            self._rule_manager = RuleManager(rules=bill_rules)
            self.search_no = self.mbl_no
        else:
            self._rule_manager = RuleManager(rules=booking_rules)
            self.search_no = self.booking_no

        self._proxy_manager = HydraproxyProxyManager(session="oolu", logger=self.logger)

    def start(self):
        option = CargoTrackingRule.build_request_option(search_no=self.search_no)
        yield self._build_request_by(option=option)

    def parse(self, response):
        yield DebugItem(info={"meta": dict(response.meta)})

        routing_rule = self._rule_manager.get_rule_by_response(response=response)

        save_name = routing_rule.get_save_name(response=response)
        self._saver.save(to=save_name, text=response.text)

        for result in routing_rule.handle(response=response):
            if isinstance(result, BaseCarrierItem):
                yield result
            elif isinstance(result, RequestOption):
                yield self._build_request_by(option=result)
            else:
                raise RuntimeError()

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
            raise ValueError(f"Invalid option.method [{option.method}]")


class ContentGetter(ChromeContentGetter):
    def __init__(self):
        super().__init__()

        self._driver.get("http://www.oocl.com/eng/Pages/default.aspx")
        time.sleep(3)
        self._is_first = True

    def search_and_return(self, search_no, search_type):
        self._search(search_no=search_no, search_type=search_type)
        time.sleep(7)
        windows = self._driver.window_handles
        self._driver.switch_to.window(windows[1])  # windows[1] is new page
        if self._is_blocked(response=Selector(text=self._driver.page_source)):
            raise RuntimeError()

        if self._is_first:
            self._is_first = False
            self._handle_with_slide()
            time.sleep(10)

        return self._driver.page_source

    def search_again_and_return(self, search_no, search_type):
        self._driver.close()

        # jump back to origin window
        windows = self.driver.window_handles
        assert len(windows) == 1
        self._driver.switch_to.window(windows[0])

        self._driver.refresh()
        time.sleep(3)
        return self.search_and_return(search_no=search_no, search_type=search_type)

    def close_current_window_and_jump_to_origin(self):
        self._driver.close()

        # jump back to origin window
        windows = self._driver.window_handles
        assert len(windows) == 1
        self._driver.switch_to.window(windows[0])

    def _search(self, search_no, search_type):
        if self._is_first:
            # handle cookies
            cookie_accept_btn = WebDriverWait(self._driver, 20).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "form > button#btn_cookie_accept"))
            )
            cookie_accept_btn.click()
            time.sleep(2)

        if self._is_first and search_type == SHIPMENT_TYPE_MBL:
            drop_down_btn = self._driver.find_element_by_css_selector("button[data-id='ooclCargoSelector']")
            drop_down_btn.click()
            bl_select = self._driver.find_element_by_css_selector("a[tabindex='0']")
            bl_select.click()

        time.sleep(2)
        search_bar = self._driver.find_element_by_css_selector("input#SEARCH_NUMBER")
        search_bar.clear()
        time.sleep(1)
        search_bar.send_keys(search_no)
        time.sleep(2)
        search_btn = self._driver.find_element_by_css_selector("a#container_btn")
        search_btn.click()

    @staticmethod
    def _is_blocked(response):
        res = response.xpath("/html/body/title/text()").extract()
        if res and str(res[0]) == "Error":
            return True
        else:
            return False

    def find_container_btn_and_click(self, container_btn_css):
        contaienr_btn = self._driver.find_element_by_css_selector(container_btn_css)
        contaienr_btn.click()

    def get_element_slide_distance(self, slider_ele, background_ele, correct=0):
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

    def refresh(self):
        refresh_button = self._driver.find_element_by_xpath(
            "/html/body/form[1]/div[4]/div[3]/div[2]/div[1]/div/div[1]/div/div/i"
        )
        refresh_button.click()
        time.sleep(5)

    def pass_verification_or_not(self):
        try:
            return self._driver.find_element_by_id("recaptcha_div")
        except NoSuchElementException:
            return None

    def _handle_with_slide(self):

        while True:
            slider_ele = self.get_slider()
            icon_ele = self.get_slider_icon_ele()
            img_ele = self.get_bg_img_ele()

            distance = self.get_element_slide_distance(icon_ele, img_ele, 0)

            if distance <= 100:
                self.refresh()
                continue

            track = self.get_track(distance)
            self.move_to_gap(slider_ele, track)

            time.sleep(5)
            if not self.pass_verification_or_not():
                break

    def get_slider(self):
        WebDriverWait(self._driver, 15).until(
            EC.presence_of_element_located(
                (By.XPATH, "/html/body/form[1]/div[4]/div[3]/div[2]/div[1]/div/div[2]/div/div/i")
            )
        )
        return self._driver.find_element_by_xpath("/html/body/form[1]/div[4]/div[3]/div[2]/div[1]/div/div[2]/div/div/i")

    def get_slider_icon_ele(self):
        canvas = self._driver.find_element_by_xpath('//*[@id="bockCanvas"]')
        canvas_base64 = self._driver.execute_script("return arguments[0].toDataURL('image/png').substring(21);", canvas)
        return canvas_base64

    def get_bg_img_ele(self):
        canvas = self._driver.find_element_by_xpath('//*[@id="imgCanvas"]')
        canvas_base64 = self._driver.execute_script("return arguments[0].toDataURL('image/png').substring(21);", canvas)
        return canvas_base64

    def move_to_gap(self, slider, track):
        ActionChains(self._driver).click_and_hold(slider).perform()

        for x in track:
            ActionChains(self._driver).move_by_offset(xoffset=x, yoffset=0).perform()
        time.sleep(0.5)  # move to the right place and take a break
        ActionChains(self._driver).release().perform()

    def get_track(self, distance):
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


# -------------------------------------------------------------------------------


class CargoTrackingRule(BaseRoutingRule):
    name = "CARGO_TRACKING"

    def __init__(self, content_getter: ContentGetter, search_type):
        self._content_getter = content_getter
        self._search_type = search_type

    @classmethod
    def build_request_option(cls, search_no: str) -> RequestOption:
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url="https://www.google.com",
            meta={
                "search_no": search_no,
            },
        )

    def get_save_name(self, response) -> str:
        return f"{self.name}.html"

    def handle(self, response):
        search_no = response.meta["search_no"]

        try:
            res = self._content_getter.search_and_return(search_no=search_no, search_type=self._search_type)
            response = Selector(text=res)

            while self._no_response(response=response):
                res = self._content_getter.search_again_and_return(search_no=search_no, search_type=self._search_type)
                response = Selector(text=res)

        except ReadTimeoutError:
            url = self._content_getter.get_current_url()
            self._content_getter.quit()
            raise LoadWebsiteTimeOutError(url=url)

        if os.path.exists("./background01.jpg"):
            os.remove("./background01.jpg")
        if os.path.exists("./slider01.jpg"):
            os.remove("./slider01.jpg")

        for item in self._handle_response(response=response, search_type=self._search_type):
            yield item

    @staticmethod
    def _no_response(response: Selector) -> bool:
        return not bool(response.css("td.pageTitle"))

    @classmethod
    def _handle_response(cls, response, search_type):
        if cls.is_search_no_invalid(response):
            raise CarrierInvalidSearchNoError(search_type=search_type)

        locator = _PageLocator()
        selector_map = locator.locate_selectors(response=response)

        search_no = cls._extract_search_no(response)
        custom_release_info = cls._extract_custom_release_info(selector_map=selector_map)
        routing_info = cls._extract_routing_info(selectors_map=selector_map)

        mbl_item = MblItem(
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

        if search_type == SHIPMENT_TYPE_MBL:
            mbl_item["mbl_no"] = search_no
        else:
            mbl_item["booking_no"] = search_no
        yield mbl_item

        container_list = cls._extract_container_list(selector_map=selector_map)
        for i, container in enumerate(container_list):
            yield ContainerStatusRule.build_request_option(
                container_no=container["container_no"].strip(),
                click_element_css=f"a[id='form:link{i}']",
            )

    @staticmethod
    def is_search_no_invalid(response):
        if response.css("span[class=noRecordBold]"):
            return True
        return False

    @classmethod
    def _extract_search_no(cls, response):
        search_no_text = response.css("th.sectionTable::text").get()
        search_no = cls._parse_search_no_text(search_no_text)
        return search_no

    @staticmethod
    def _parse_search_no_text(search_no_text):
        # Search Result - Bill of Lading Number  2109051600
        # Search Result - Booking Number  2636035340
        pattern = re.compile(r"^Search\s+Result\s+-\s+(Bill\s+of\s+Lading|Booking)\s+Number\s+(?P<search_no>\d+)\s+$")
        match = pattern.match(search_no_text)
        if not match:
            raise CarrierResponseFormatError(reason=f"Unknown search_no_text: `{search_no_text}`")
        return match.group("search_no")

    @classmethod
    def _extract_custom_release_info(cls, selector_map: Dict[str, scrapy.Selector]):
        table = selector_map["summary:main_right_table"]

        table_locator = SummaryRightTableLocator()
        table_locator.parse(table)
        table_extractor = TableExtractor(table_locator)
        first_td_extractor = FirstTextTdExtractor()

        if not table_extractor.has_header(top="Inbound Customs Clearance Status:"):
            return {
                "status": "",
                "date": "",
            }

        custom_release_info = table_extractor.extract_cell(
            top="Inbound Customs Clearance Status:", left=None, extractor=first_td_extractor
        )
        custom_release_status, custom_release_date = cls._parse_custom_release_info(custom_release_info)

        return {
            "status": custom_release_status.strip(),
            "date": custom_release_date.strip(),
        }

    @staticmethod
    def _parse_custom_release_info(custom_release_info):
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
            raise CarrierResponseFormatError(reason=f"Unknown custom_release_info: `{custom_release_info}`")
        return match.group("status").strip(), match.group("date") or ""

    @staticmethod
    def _extract_routing_info(selectors_map: Dict[str, scrapy.Selector]):
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
            }

        table_locator = RoutingTableLocator()
        table_locator.parse(table=table)
        table_extractor = TableExtractor(table_locator=table_locator)
        span_extractor = FirstTextTdExtractor("span::text")

        # vessel_voyage
        vessel_voyage_extractor = VesselVoyageTdExtractor()
        vessel_voyage = table_extractor.extract_cell(
            top="Vessel Voyage", left=table_locator.LAST_LEFT_HEADER, extractor=vessel_voyage_extractor
        )

        # por
        por = table_extractor.extract_cell(top="Origin", left=table_locator.FIRST_LEFT_HEADER, extractor=span_extractor)

        # pol / pod
        pol_pod_extractor = PolPodTdExtractor()

        pol_info = table_extractor.extract_cell(
            top="Port of Load", left=table_locator.FIRST_LEFT_HEADER, extractor=pol_pod_extractor
        )
        etd, atd = _get_est_and_actual(status=pol_info["status"], time_str=pol_info["time_str"])

        pod_info = table_extractor.extract_cell(
            top="Port of Discharge", left=table_locator.LAST_LEFT_HEADER, extractor=pol_pod_extractor
        )
        eta, ata = _get_est_and_actual(status=pod_info["status"], time_str=pod_info["time_str"])

        # place_of_deliv
        deliv_extractor = DelivTdExtractor()
        deliv_info = table_extractor.extract_cell(
            top="Final Destination Hub", left=table_locator.LAST_LEFT_HEADER, extractor=deliv_extractor
        )
        deliv_eta, deliv_ata = _get_est_and_actual(status=deliv_info["status"], time_str=deliv_info["time_str"])

        # final_dest
        final_dest = table_extractor.extract_cell(
            top="Destination", left=table_locator.LAST_LEFT_HEADER, extractor=span_extractor
        )

        return {
            "por": por,
            "pol": pol_info["port"],
            "pod": pod_info["port"],
            "place_of_deliv": deliv_info["port"],
            "final_dest": final_dest,
            "etd": etd,
            "atd": atd,
            "eta": eta,
            "ata": ata,
            "deliv_eta": deliv_eta,
            "deliv_ata": deliv_ata,
            "vessel": vessel_voyage["vessel"],
            "voyage": vessel_voyage["voyage"],
        }

    @staticmethod
    def _extract_container_list(selector_map: Dict[str, scrapy.Selector]):
        table = selector_map["summary:container_table"]

        container_table_locator = ContainerTableLocator()
        container_table_locator.parse(table=table)
        table_extractor = TableExtractor(table_locator=container_table_locator)

        container_no_list = []
        for left in container_table_locator.iter_left_headers():
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


class SummaryRightTableLocator(BaseTableLocator):
    TD_TITLE_INDEX = 0
    TD_DATA_INDEX = 1

    def __init__(self):
        self._td_map = {}  # title: td

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

            self._td_map[title] = data_td

    def get_cell(self, top, left) -> Selector:
        assert left is None
        try:
            return self._td_map[top]
        except (KeyError, IndexError) as err:
            raise HeaderMismatchError(repr(err))

    def has_header(self, top=None, left=None) -> bool:
        return (top in self._td_map) and (left is None)


class RoutingTableLocator(BaseTableLocator):
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

    def __init__(self):
        self._td_map = {}  # title: [td, ...]

    def parse(self, table: scrapy.Selector):
        title_tr = table.css("tr")[self.TR_TITLE_INDEX]
        data_trs = table.css("tr")[self.TR_DATA_START_INDEX :]

        raw_title_list = title_tr.css("th::text").getall()
        title_list = [title.strip() for title in raw_title_list if isinstance(title, str)]

        for title_index, title in enumerate(title_list):
            data_index = title_index

            self._td_map[title] = []
            for data_tr in data_trs:
                data_td = data_tr.css("td")[data_index]
                self._td_map[title].append(data_td)

    def get_cell(self, top, left) -> scrapy.Selector:
        try:
            return self._td_map[top][left]
        except KeyError as err:
            raise HeaderMismatchError(repr(err))

    def has_header(self, top=None, left=None) -> bool:
        return (top in self._td_map) and (left is None)


class ContainerTableLocator(BaseTableLocator):
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

    def __init__(self):
        self._td_map = {}  # title: [td, ...]
        self._data_len = 0

    def parse(self, table: scrapy.Selector):
        tr_list = table.xpath("./tr") or table.xpath("./tbody/tr")

        main_title_list = tr_list[self.TR_MAIN_TITLE_INDEX].css("th::text").getall()
        sub_title_list = tr_list[self.TR_SUB_TITLE_INDEX].css("th::text").getall()
        data_tr_list = tr_list[self.TR_DATA_START_INDEX :]

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

        first_title = title_list[0]
        self._data_len = len(self._td_map[first_title])

    def get_cell(self, top, left) -> scrapy.Selector:
        try:
            return self._td_map[top][left]
        except KeyError as err:
            raise HeaderMismatchError(repr(err))

    def has_header(self, top=None, left=None) -> bool:
        return (top in self._td_map) and (left is None)

    def iter_left_headers(self):
        for index in range(self._data_len):
            yield index


class VesselVoyageTdExtractor(BaseTableCellExtractor):
    def extract(self, cell: Selector):
        text_list = cell.css("::text").getall()

        if len(text_list) != 2:
            CarrierResponseFormatError(reason=f"Unknown Vessel Voyage td format: `{text_list}`")

        vessel = self._parse_vessel(text_list[0])

        return {
            "vessel": vessel,
            "voyage": text_list[1].strip(),
        }

    @staticmethod
    def _parse_vessel(text):
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
    def extract(self, cell: Selector):
        text_list = cell.css("::text").getall()

        if len(text_list) < 4:
            raise CarrierResponseFormatError(reason=f"Unknown Pol or Pod td format: `{text_list}`")

        return {
            "port": text_list[0].strip(),
            "time_str": text_list[2].strip(),
            "status": text_list[3].strip(),
        }


class DelivTdExtractor(BaseTableCellExtractor):
    def extract(self, cell: Selector):
        text_list = cell.css("::text").getall()

        if len(text_list) < 3:
            raise CarrierResponseFormatError(reason=f"Unknown Deliv td format: `{text_list}`")

        return {
            "port": text_list[0].strip(),
            "time_str": text_list[1].strip(),
            "status": text_list[2].strip(),
        }


class ContainerStatusRule(BaseRoutingRule):
    name = "CONTAINER_STATUS"

    def __init__(self, content_getter: ContentGetter):
        self._content_getter = content_getter

    @classmethod
    def build_request_option(cls, container_no: str, click_element_css: str) -> RequestOption:
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url="https://www.google.com",
            meta={
                "container_no": container_no,
                "click_element_css": click_element_css,
            },
        )

    @staticmethod
    def transform_cookies_to_str(cookies: Dict):
        cookies_str = ""
        for key, value in cookies.items():
            cookies_str += f"{key}={value}; "

        return cookies_str[:-2]

    def get_save_name(self, response) -> str:
        container_no = response.meta["container_no"]
        return f"{self.name}_{container_no}.html"

    def handle(self, response):
        container_no = response.meta["container_no"]
        click_element_css = response.meta["click_element_css"]

        try:
            self._content_getter.find_container_btn_and_click(container_btn_css=click_element_css)
            time.sleep(10)
        except ReadTimeoutError:
            url = self._content_getter.get_current_url()
            self._content_getter.quit()
            raise LoadWebsiteTimeOutError(url=url)

        response = Selector(text=self._content_getter.get_page_source())

        for item in self._handle_response(response=response, container_no=container_no):
            yield item

    @classmethod
    def _handle_response(cls, response, container_no):
        locator = _PageLocator()
        selectors_map = locator.locate_selectors(response=response)
        detention_info = cls._extract_detention_info(selectors_map)

        yield ContainerItem(
            container_key=container_no,
            container_no=container_no,
            last_free_day=detention_info["last_free_day"] or None,
            det_free_time_exp_date=detention_info["det_free_time_exp_date"] or None,
        )

        container_status_list = cls._extract_container_status_list(selectors_map)
        for container_status in container_status_list:
            event = container_status["event"].strip()
            facility = container_status["facility"]

            if facility:
                description = f"{event} ({facility})"
            else:
                description = event

            yield ContainerStatusItem(
                container_key=container_no,
                description=description,
                location=LocationItem(name=container_status["location"]),
                transport=container_status["transport"],
                local_date_time=container_status["local_date_time"],
            )

    @staticmethod
    def _extract_detention_info(selectors_map: Dict[str, scrapy.Selector]):
        table = selectors_map.get("detail:detention_right_table", None)
        if table is None:
            return {
                "last_free_day": "",
                "det_free_time_exp_date": "",
            }

        table_locator = DestinationTableLocator()
        table_locator.parse(table=table)
        table_extractor = TableExtractor(table_locator=table_locator)
        td_extractor = DetentionDateTdExtractor()

        if table_locator.has_header(left="Demurrage Last Free Date:"):
            lfd_info = table_extractor.extract_cell(top=None, left="Demurrage Last Free Date:", extractor=td_extractor)
            _, lfd = _get_est_and_actual(status=lfd_info["status"], time_str=lfd_info["time_str"])
        else:
            lfd = ""

        if table_locator.has_header(left="Detention Last Free Date:"):
            det_lfd_info = table_extractor.extract_cell(
                top=None, left="Detention Last Free Date:", extractor=td_extractor
            )
            _, det_lfd = _get_est_and_actual(status=det_lfd_info["status"], time_str=det_lfd_info["time_str"])
        else:
            det_lfd = ""

        return {
            "last_free_day": lfd,
            "det_free_time_exp_date": det_lfd,
        }

    @staticmethod
    def _extract_container_status_list(selectors_map: Dict[str, scrapy.Selector]):
        table = selectors_map.get("detail:container_status_table", None)
        if table is None:
            return []

        table_locator = ContainerStatusTableLocator()
        table_locator.parse(table=table)
        table_extractor = TableExtractor(table_locator=table_locator)
        first_text_extractor = FirstTextTdExtractor()
        span_extractor = FirstTextTdExtractor(css_query="span::text")

        container_status_list = []
        for left in table_locator.iter_left_headers():
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


class ContainerStatusTableLocator(BaseTableLocator):
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

    def __init__(self):
        self._td_map = {}  # title: [td, ...]
        self._data_len = 0

    def parse(self, table: scrapy.Selector):
        title_list = table.css("th::text").getall()
        data_tr_list = table.css("tr")[self.DATA_START_TR_INDEX :]

        for title_index, title in enumerate(title_list):
            data_index = title_index

            title = title.strip()
            self._td_map[title] = []
            for data_tr in data_tr_list:
                data_td = data_tr.css("td")[data_index]
                self._td_map[title].append(data_td)

        first_title = title_list[0]
        self._data_len = len(self._td_map[first_title])

    def get_cell(self, top, left) -> scrapy.Selector:
        try:
            return self._td_map[top][left]
        except KeyError as err:
            raise HeaderMismatchError(repr(err))

    def has_header(self, top=None, left=None) -> bool:
        return (top in self._td_map) and (left is None)

    def iter_left_headers(self):
        for index in range(self._data_len):
            yield index


class DestinationTableLocator(BaseTableLocator):
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

    TITEL_TD_INDEX = 0
    DATA_NEEDED_TD_INDEX = 2

    def __init__(self):
        self._td_map = {}  # title: td

    def parse(self, table: scrapy.Selector):
        tr_list = table.css("tr")

        for tr in tr_list:
            td_list = tr.css("td")

            title_td = td_list[self.TITEL_TD_INDEX]
            title = title_td.css("::text").get()
            title = title.strip() if isinstance(title, str) else ""
            self._td_map[title] = td_list[self.DATA_NEEDED_TD_INDEX]

    def get_cell(self, top, left) -> scrapy.Selector:
        assert top is None
        try:
            return self._td_map[left]
        except KeyError as err:
            raise HeaderMismatchError(repr(err))

    def has_header(self, top=None, left=None) -> bool:
        return (left in self._td_map) and (top is None)


class DetentionDateTdExtractor(BaseTableCellExtractor):
    def extract(self, cell: Selector):
        text_list = cell.css("::text").getall()
        text_list_len = len(text_list)

        if text_list_len != 2 or text_list_len != 1:
            CarrierResponseFormatError(reason=f"Unknown last free day td format: `{text_list}`")

        return {
            "time_str": text_list[0].strip(),
            "status": text_list[1].strip() if text_list_len == 2 else "",
        }


# -------------------------------------------------------------------------------


class _PageLocator:
    def locate_selectors(self, response: scrapy.Selector):
        tables = response.css("table.groupTable")

        # summary
        summary_rule = CssQueryTextStartswithMatchRule(css_query="td.groupTitle::text", startswith="Summary")
        summary_table = find_selector_from(selectors=tables, rule=summary_rule)
        if not summary_table:
            raise CarrierResponseFormatError(reason="Can not find summary table !!!")
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

    @staticmethod
    def _locate_selectors_from_summary(summary_table: scrapy.Selector):
        # top table
        top_table = summary_table.xpath("./tr/td/table") or summary_table.xpath("./tbody/tr/td/table")
        if not top_table:
            raise CarrierResponseFormatError(reason="Can not find top_table !!!")

        top_inner_tables = top_table.xpath("./tr/td") or top_table.xpath("./tbody/tr/td")
        if len(top_inner_tables) != 2:
            raise CarrierResponseFormatError(reason=f"Amount of top_inner_tables not right: `{len(top_inner_tables)}`")

        # bottom table
        bottom_table = summary_table.css("div#summaryDiv > table")
        if not bottom_table:
            raise CarrierResponseFormatError(reason="Can not find container_outer_table !!!")

        bottom_inner_tables = bottom_table.css("tr table")
        if not bottom_inner_tables:
            raise CarrierResponseFormatError(reason="Can not find container_inner_table !!!")

        return {
            "summary:main_left_table": top_inner_tables[0],
            "summary:main_right_table": top_inner_tables[1],
            "summary:container_table": bottom_inner_tables[0],
        }

    def _locate_selectors_from_detail(self, detail_table: scrapy.Selector):
        # routing tab
        routing_tab = detail_table.css("div#Tab1")
        if not routing_tab:
            raise CarrierResponseFormatError(reason="Can not find routing_tab !!!")

        routing_table = routing_tab.css("table#eventListTable")
        if not routing_table:
            raise CarrierResponseFormatError(reason="Can not find routing_table !!!")

        # equipment tab
        equipment_tab = detail_table.css("div#Tab2")
        if not equipment_tab:
            raise CarrierResponseFormatError(reason="Can not find equipment_tab !!!")

        equipment_table = equipment_tab.css("table#eventListTable")
        if not equipment_table:
            raise CarrierResponseFormatError(reason="Can not find equipment_table !!!")

        # detention tab
        detention_tab = detail_table.css("div#Tab3")
        if not detention_tab:
            raise CarrierResponseFormatError(reason="Can not find detention_tab !!!")

        detention_tables = self._locate_detail_detention_tables(detention_tab=detention_tab)

        return {
            "detail:routing_table": routing_table,
            "detail:container_status_table": equipment_table,
            "detail:detention_right_table": detention_tables[1],
        }

    @staticmethod
    def _locate_detail_detention_tables(detention_tab: scrapy.Selector):
        inner_parts = detention_tab.xpath("./table/tr/td/table") or detention_tab.xpath("./table/tbody/tr/td/table")
        if len(inner_parts) != 2:
            raise CarrierResponseFormatError(reason=f"Amount of detention_inner_parts not right: `{len(inner_parts)}`")

        title_part, content_part = inner_parts

        detention_tables = content_part.xpath("./tr/td/table/tr/td/table") or content_part.xpath(
            "./tbody/tr/td/table/tbody/tr/td/table"
        )
        if len(detention_tables) != 2:
            raise CarrierResponseFormatError(
                reason=f"Amount of detention tables does not right: {len(detention_tables)}"
            )

        return detention_tables


def _get_est_and_actual(status, time_str):
    if status == "(Actual)":
        estimate, actual = None, time_str
    elif status == "(Estimated)":
        estimate, actual = time_str, ""
    elif status == "":
        estimate, actual = None, ""
    else:
        raise CarrierResponseFormatError(reason=f"Unknown status format: `{status}`")

    return estimate, actual


def get_multipart_body(form_data, boundary):
    body = ""
    for index, key in enumerate(form_data):
        body += f"--{boundary}\r\n" f'Content-Disposition: form-data; name="{key}"\r\n' f"\r\n" f"{form_data[key]}\r\n"
    body += f"--{boundary}--"
    return body
