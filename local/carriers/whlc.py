import dataclasses
import asyncio
import logging

from scrapy import Selector
from pyppeteer.errors import TimeoutError, ElementHandleError
from urllib3.exceptions import ReadTimeoutError

from local.core import BaseLocalCrawler
from local.proxy import HydraproxyProxyManager, ProxyManager
from src.crawler.core_carrier.exceptions import LoadWebsiteTimeOutError
from src.crawler.core_carrier.base import SHIPMENT_TYPE_MBL, SHIPMENT_TYPE_BOOKING
from src.crawler.core_carrier.exceptions import (
    LoadWebsiteTimeOutError,
    CarrierInvalidSearchNoError,
    CARRIER_RESULT_STATUS_ERROR,
)
from src.crawler.core_carrier.items import (
    MblItem,
    LocationItem,
    VesselItem,
    ContainerItem,
    ContainerStatusItem,
    ExportErrorData,
)
from src.crawler.core.pyppeteer import PyppeteerContentGetter
from src.crawler.spiders.carrier_whlc_multi import BookingRoutingRule, MblRoutingRule

WHLC_BASE_URL = "https://www.wanhai.com/views/cargoTrack/CargoTrack.xhtml"


@dataclasses.dataclass
class ProxyOption:
    group: str
    session: str


logger = logging.getLogger("local-crawler-whlc")


class WhlcContentGetter(PyppeteerContentGetter):
    def __init__(self, proxy_manager: ProxyManager = None):
        super().__init__(proxy_manager)
        self._type_select_num_map = {
            SHIPMENT_TYPE_MBL: "2",
            SHIPMENT_TYPE_BOOKING: "4",
        }

    async def multi_search(self, search_nos, search_type):
        await self.page.goto(WHLC_BASE_URL, options={"timeout": 60000})
        await asyncio.sleep(3)
        select_num = self._type_select_num_map[search_type]
        await self.page.waitForSelector("#cargoType")
        await self.page.select("#cargoType", select_num)
        await asyncio.sleep(1)
        for i, search_no in enumerate(search_nos, start=1):
            await self.page.type(f"#q_ref_no{i}", search_no)
            await asyncio.sleep(0.5)
        await asyncio.sleep(3)
        await self.page.click("#Query")
        await asyncio.sleep(10)
        await self.switch_to_last()
        await self.page.waitForSelector("table.tbl-list")
        await asyncio.sleep(5)
        return await self.page.content()

    async def go_detail_page(self, idx: int):
        await self.page.waitForSelector(
            f"#cargoTrackListBean > table > tbody > tr:nth-child({idx}) > td:nth-child(1) > u"
        )
        await self.page.click(f"#cargoTrackListBean > table > tbody > tr:nth-child({idx}) > td:nth-child(1) > u")
        await asyncio.sleep(10)
        await self.switch_to_last()
        await self.page.waitForSelector("table.tbl-list")
        await asyncio.sleep(3)
        return await self.page.content()

    async def go_history_page(self, idx: int):
        await self.page.waitForSelector(
            f"#cargoTrackListBean > table > tbody > tr:nth-child({idx}) > td:nth-child(11) > u"
        ),
        await self.page.click(f"#cargoTrackListBean > table > tbody > tr:nth-child({idx}) > td:nth-child(11) > u"),
        await asyncio.sleep(10)
        await self.switch_to_last()
        await self.page.waitForSelector("table.tbl-list")
        await asyncio.sleep(3)
        return await self.page.content()

    async def go_booking_history_page(self, idx: int):
        await self.page.waitForSelector(
            f"#cargoTrackListBean > table > tbody > tr:nth-child({idx}) > td:nth-child(2) > a"
        ),
        await self.page.click(f"#cargoTrackListBean > table > tbody > tr:nth-child({idx}) > td:nth-child(2) > a"),
        await asyncio.sleep(10),
        await self.switch_to_last()
        await self.page.waitForSelector("table.tbl-list")
        await asyncio.sleep(3)
        return await self.page.content()

    async def switch_to_last(self):
        pages = await self.browser.pages()
        self.page = pages[-1]
        await asyncio.sleep(3)

    async def close_page(self):
        await self.page.close()
        await asyncio.sleep(1)

    def close_page_and_switch_last(self):
        asyncio.get_event_loop().run_until_complete(self.close_page())
        asyncio.get_event_loop().run_until_complete(self.switch_to_last())


class WhlcLocalCrawler(BaseLocalCrawler):
    code = "WHLC"

    def __init__(self):
        super().__init__()
        self.content_getter = WhlcContentGetter(proxy_manager=HydraproxyProxyManager(logger=logger))
        self._search_type = ""

    def start_crawler(self, task_ids: str, mbl_nos: str, booking_nos: str, container_nos: str):
        task_ids = task_ids.split(",")
        if mbl_nos:
            mbl_nos = mbl_nos.split(",")
            self._search_type = SHIPMENT_TYPE_MBL
            for item in self.handle_mbl(mbl_nos, task_ids):
                yield item
        elif booking_nos:
            booking_nos = booking_nos.split(",")
            self._search_type = SHIPMENT_TYPE_BOOKING
            for item in self.handle_booking(booking_nos, task_ids):
                yield item

    def handle_mbl(self, mbl_nos, task_ids):
        rule = MblRoutingRule(self.content_getter)

        try:
            page_source = asyncio.get_event_loop().run_until_complete(
                self.content_getter.multi_search(search_nos=mbl_nos, search_type=self._search_type)
            )
            response_selector = Selector(text=page_source)
            container_list = rule.extract_container_info(response_selector)
            mbl_no_set = rule.get_mbl_no_set_from(container_list=container_list)
        except ReadTimeoutError:
            raise LoadWebsiteTimeOutError(url=WHLC_BASE_URL)

        for mbl_no, task_id in zip(mbl_nos, task_ids):
            if mbl_no in mbl_no_set:
                yield MblItem(task_id=task_id, mbl_no=mbl_no)
            else:
                yield ExportErrorData(
                    task_id=task_id, mbl_no=mbl_no, status=CARRIER_RESULT_STATUS_ERROR, detail="Data was not found"
                )
                continue

        for idx in range(len(container_list)):
            container_no = container_list[idx]["container_no"]
            mbl_no = container_list[idx]["mbl_no"]
            index = mbl_nos.index(mbl_no)
            task_id = task_ids[index]

            yield ContainerItem(
                task_id=task_id,
                container_key=container_no,
                container_no=container_no,
            )

            # detail page
            try:
                for item in self.handle_detail_page(task_id, idx):
                    yield item
            except ElementHandleError:
                pass
            except TimeoutError:
                yield ExportErrorData(
                    task_id=task_id,
                    mbl_no=mbl_no,
                    status=CARRIER_RESULT_STATUS_ERROR,
                    detail="Load detail page timeout",
                )
                self.content_getter.close_page_and_switch_last()
                continue

            # history page
            try:
                for item in self.handle_history_page(task_id, container_no, idx):
                    yield item
            except ElementHandleError:
                pass
            except TimeoutError:
                yield ExportErrorData(
                    task_id=task_id,
                    mbl_no=mbl_no,
                    status=CARRIER_RESULT_STATUS_ERROR,
                    detail="Load status page timeout",
                )
                self.content_getter.close_page_and_switch_last()
                continue

            self.content_getter.close_page_and_switch_last()

    def handle_detail_page(self, task_id, idx):
        page_source = asyncio.get_event_loop().run_until_complete(self.content_getter.go_detail_page(idx + 2))
        detail_selector = Selector(text=page_source)
        date_information = MblRoutingRule.extract_date_information(detail_selector)

        yield VesselItem(
            task_id=task_id,
            vessel_key=f"{date_information['pol_vessel']} / {date_information['pol_voyage']}",
            vessel=date_information["pol_vessel"],
            voyage=date_information["pol_voyage"],
            pol=LocationItem(un_lo_code=date_information["pol_un_lo_code"]),
            etd=date_information["pol_etd"],
        )

        yield VesselItem(
            task_id=task_id,
            vessel_key=f"{date_information['pod_vessel']} / {date_information['pod_voyage']}",
            vessel=date_information["pod_vessel"],
            voyage=date_information["pod_voyage"],
            pod=LocationItem(un_lo_code=date_information["pod_un_lo_code"]),
            eta=date_information["pod_eta"],
        )

        self.content_getter.close_page_and_switch_last()

    def handle_history_page(self, task_id, container_no, idx):
        page_source = asyncio.get_event_loop().run_until_complete(self.content_getter.go_history_page(idx + 2))
        history_selector = Selector(text=page_source)
        container_status_list = MblRoutingRule.extract_container_status(history_selector)

        for container_status in container_status_list:
            yield ContainerStatusItem(
                task_id=task_id,
                container_key=container_no,
                local_date_time=container_status["local_date_time"],
                description=container_status["description"],
                location=LocationItem(name=container_status["location_name"]),
            )

    def handle_booking(self, booking_nos, task_ids):
        rule = BookingRoutingRule()
        page_source = asyncio.get_event_loop().run_until_complete(
            self.content_getter.multi_search(search_nos=booking_nos, search_type=self._search_type)
        )

        response_selector = Selector(text=page_source)
        if rule.is_search_no_invalid(response=response_selector):
            raise CarrierInvalidSearchNoError(search_type=self._search_type)
        booking_list = rule.extract_booking_list(response_selector)
        book_no_set = rule.get_book_no_set_from(booking_list=booking_list)

        for task_id, search_no in zip(task_ids, booking_nos):
            if search_no not in book_no_set:
                yield ExportErrorData(
                    task_id=task_id,
                    booking_no=search_no,
                    status=CARRIER_RESULT_STATUS_ERROR,
                    detail="Data was not found",
                )

        for b_idx in range(len(booking_list)):
            search_no = booking_list[b_idx]["booking_no"]
            index = booking_nos.index(search_no)
            task_id = task_ids[index]
            try:
                page_source = asyncio.get_event_loop().run_until_complete(self.content_getter.go_detail_page(b_idx + 2))
            except TimeoutError:
                yield ExportErrorData(
                    task_id=task_id,
                    booking_no=search_no,
                    status=CARRIER_RESULT_STATUS_ERROR,
                    detail="Load detail page timeout",
                )
                self.content_getter.close_page_and_switch_last()
                continue
            for item in self.handle_booking_detail_page(response=page_source, task_id=task_id, search_no=search_no):
                yield item

            for item in self.handle_booking_history_page(response=page_source, task_id=task_id, search_no=search_no):
                yield item

            self.content_getter.close_page_and_switch_last()

    def handle_booking_detail_page(self, response, task_id, search_no):
        basic_info = BookingRoutingRule.extract_basic_info(Selector(text=response))
        vessel_info = BookingRoutingRule.extract_vessel_info(Selector(text=response))

        yield MblItem(
            task_id=task_id,
            booking_no=search_no,
        )

        yield VesselItem(
            task_id=task_id,
            vessel_key=f"{basic_info['vessel']} / {basic_info['voyage']}",
            vessel=basic_info["vessel"],
            voyage=basic_info["voyage"],
            pol=LocationItem(name=vessel_info["pol"]),
            etd=vessel_info["etd"],
        )

        yield VesselItem(
            task_id=task_id,
            vessel_key=f"{basic_info['vessel']} / {basic_info['voyage']}",
            vessel=basic_info["vessel"],
            voyage=basic_info["voyage"],
            pod=LocationItem(name=vessel_info["pod"]),
            eta=vessel_info["eta"],
        )

    def handle_booking_history_page(self, response, task_id, search_no):
        container_nos = BookingRoutingRule.extract_container_no_and_status_links(Selector(text=response))

        for idx in range(len(container_nos)):
            container_no = container_nos[idx]
            # history page
            try:
                page_source = asyncio.get_event_loop().run_until_complete(
                    self.content_getter.go_booking_history_page(idx + 2)
                )
            except TimeoutError:
                yield ExportErrorData(
                    task_id=task_id,
                    booking_no=search_no,
                    status=CARRIER_RESULT_STATUS_ERROR,
                    detail="Load status page timeout",
                )
                self.content_getter.close_page_and_switch_last()
                continue
            history_selector = Selector(text=page_source)

            event_list = BookingRoutingRule.extract_container_status(response=history_selector)
            container_status_items = BookingRoutingRule.make_container_status_items(task_id, container_no, event_list)

            yield ContainerItem(
                task_id=task_id,
                container_key=container_no,
                container_no=container_no,
            )

            for item in container_status_items:
                yield item

            self.content_getter.close_page_and_switch_last()
