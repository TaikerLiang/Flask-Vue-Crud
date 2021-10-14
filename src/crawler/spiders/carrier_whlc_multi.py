import re
import asyncio
from urllib3.exceptions import ReadTimeoutError
from typing import List, Dict

import scrapy
from scrapy import Selector
from pyppeteer import launch, logging
from pyppeteer.errors import TimeoutError, ElementHandleError

from crawler.core_carrier.base import CARRIER_RESULT_STATUS_FATAL, SHIPMENT_TYPE_MBL, SHIPMENT_TYPE_BOOKING
from crawler.core_carrier.base_spiders import BaseMultiCarrierSpider
from crawler.core_carrier.request_helpers import RequestOption
from crawler.core_carrier.rules import RuleManager, BaseRoutingRule, RequestOptionQueue
from crawler.core_carrier.items import (
    MblItem, BaseCarrierItem, LocationItem, VesselItem, ContainerItem, ContainerStatusItem, ExportErrorData, DebugItem)
from crawler.core_carrier.exceptions import CarrierResponseFormatError, LoadWebsiteTimeOutError, BaseCarrierError, \
    SuspiciousOperationError, CarrierInvalidSearchNoError, CARRIER_RESULT_STATUS_ERROR
from crawler.extractors.selector_finder import BaseMatchRule, find_selector_from
from crawler.extractors.table_cell_extractors import BaseTableCellExtractor
from crawler.extractors.table_extractors import BaseTableLocator, HeaderMismatchError, TableExtractor

WHLC_BASE_URL = 'https://www.wanhai.com/views/cargoTrack/CargoTrack.xhtml'
COOKIES_RETRY_LIMIT = 3


class CarrierWhlcSpider(BaseMultiCarrierSpider):
    name = 'carrier_whlc_multi'

    def __init__(self, *args, **kwargs):
        super(CarrierWhlcSpider, self).__init__(*args, **kwargs)

        bill_rules = [
            MblRoutingRule()
        ]

        booking_rules = [
            BookingRoutingRule()
        ]

        if self.search_type == SHIPMENT_TYPE_MBL:
            self._rule_manager = RuleManager(rules=bill_rules)
        elif self.search_type == SHIPMENT_TYPE_BOOKING:
            self._rule_manager = RuleManager(rules=booking_rules)

        self._request_queue = RequestOptionQueue()

    def start(self):
        if self.search_type == SHIPMENT_TYPE_MBL:
            request_option = MblRoutingRule.build_request_option(mbl_nos=self.search_nos, task_ids=self.task_ids)
            yield self._build_request_by(option=request_option)
        else:
            request_option = BookingRoutingRule.build_request_option(search_nos=self.search_nos, task_ids=self.task_ids)
            yield self._build_request_by(option=request_option)

    def parse(self, response):
        yield DebugItem(info={'meta': dict(response.meta)})

        routing_rule = self._rule_manager.get_rule_by_response(response=response)

        save_name = routing_rule.get_save_name(response=response)
        self._saver.save(to=save_name, text=response.text)

        for result in routing_rule.handle(response=response):
            if isinstance(result, BaseCarrierItem):
                yield result
            elif isinstance(result, RequestOption):
                self._request_queue.add_request(result)
            else:
                raise RuntimeError()

        if not self._request_queue.is_empty():
            request_option = self._request_queue.get_next_request()
            yield self._build_request_by(option=request_option)

    def _build_request_by(self, option: RequestOption):
        meta = {
            RuleManager.META_CARRIER_CORE_RULE_NAME: option.rule_name,
            **option.meta,
        }

        if option.method == RequestOption.METHOD_POST_BODY:
            return scrapy.Request(
                url=option.url,
                headers=option.headers,
                meta=meta,
                callback=self.parse,
                method='POST',
                body=option.body,
                dont_filter=True,
            )
        elif option.method == RequestOption.METHOD_GET:
            return scrapy.Request(
                url=option.url,
                headers=option.headers,
                cookies=option.cookies,
                meta=meta,
                dont_filter=True,
            )
        else:
            raise SuspiciousOperationError(msg=f'Unexpected request method: `{option.method}`')


# -------------------------------------------------------------------------------


class CarrierIpBlockError(BaseCarrierError):
    status = CARRIER_RESULT_STATUS_FATAL

    def build_error_data(self):
        return ExportErrorData(status=self.status, detail='<ip-block-error>')


class MblRoutingRule(BaseRoutingRule):
    name = 'MBL_RULE'

    def __init__(self):
        self._container_patt = re.compile(r'^(?P<container_no>\w+)')
        self._j_idt_patt = re.compile(r"'(?P<j_idt>j_idt[^,]+)':'(?P=j_idt)'")
        self._search_type = SHIPMENT_TYPE_MBL
        self.driver = WhlcContentGetter()

    @classmethod
    def build_request_option(cls, mbl_nos, task_ids):
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=f'https://google.com',
            meta={
                'mbl_nos': mbl_nos,
                'task_ids': task_ids
            },
        )

    def handle(self, response):
        task_ids = response.meta['task_ids']
        mbl_nos = response.meta['mbl_nos']
        try:
            asyncio.get_event_loop().run_until_complete(self.driver.launch_and_go())
            page_source = asyncio.get_event_loop().run_until_complete(
                self.driver.multi_search(search_nos=mbl_nos, search_type=self._search_type))
        except ReadTimeoutError:
            raise LoadWebsiteTimeOutError(url=WHLC_BASE_URL)

        response_selector = Selector(text=page_source)
        container_list = self.extract_container_info(response_selector)
        mbl_no_set = self.get_mbl_no_set_from(container_list=container_list)

        for mbl_no, task_id in zip(mbl_nos, task_ids):
            if mbl_no in mbl_no_set:
                yield MblItem(
                    task_id=task_id,
                    mbl_no=mbl_no
                )
            else:
                yield ExportErrorData(task_id=task_id, mbl_no=mbl_no, status=CARRIER_RESULT_STATUS_ERROR,
                                      detail='Data was not found')
                continue

        for idx in range(len(container_list)):
            container_no = container_list[idx]['container_no']
            mbl_no = container_list[idx]['mbl_no']
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
                yield ExportErrorData(task_id=task_id, mbl_no=mbl_no, status=CARRIER_RESULT_STATUS_ERROR,
                                      detail='Load detail page timeout')
                self.driver.close_page_and_switch_last()
                continue

            # history page
            try:
                for item in self.handle_history_page(task_id, container_no, idx):
                    yield item
            except ElementHandleError:
                pass
            except TimeoutError:
                yield ExportErrorData(task_id=task_id, mbl_no=mbl_no, status=CARRIER_RESULT_STATUS_ERROR,
                                      detail='Load status page timeout')
                self.driver.close_page_and_switch_last()
                continue

            self.driver.close_page_and_switch_last()
        asyncio.get_event_loop().run_until_complete(self.driver.close())

    def get_save_name(self, response) -> str:
        return f'{self.name}.html'

    def handle_detail_page(self, task_id, idx):
        page_source = asyncio.get_event_loop().run_until_complete(self.driver.go_detail_page(idx + 2))
        detail_selector = Selector(text=page_source)
        date_information = self.extract_date_information(detail_selector)

        yield VesselItem(
            task_id=task_id,
            vessel_key=f"{date_information['pol_vessel']} / {date_information['pol_voyage']}",
            vessel=date_information['pol_vessel'],
            voyage=date_information['pol_voyage'],
            pol=LocationItem(un_lo_code=date_information['pol_un_lo_code']),
            etd=date_information['pol_etd'],
        )

        yield VesselItem(
            task_id=task_id,
            vessel_key=f"{date_information['pod_vessel']} / {date_information['pod_voyage']}",
            vessel=date_information['pod_vessel'],
            voyage=date_information['pod_voyage'],
            pod=LocationItem(un_lo_code=date_information['pod_un_lo_code']),
            eta=date_information['pod_eta'],
        )

        self.driver.close_page_and_switch_last()

    def handle_history_page(self, task_id, container_no, idx):
        page_source = asyncio.get_event_loop().run_until_complete(self.driver.go_history_page(idx + 2))
        history_selector = Selector(text=page_source)
        container_status_list = self.extract_container_status(history_selector)

        for container_status in container_status_list:
            yield ContainerStatusItem(
                task_id=task_id,
                container_key=container_no,
                local_date_time=container_status['local_date_time'],
                description=container_status['description'],
                location=LocationItem(name=container_status['location_name']),
            )

    def extract_container_info(self, response: scrapy.Selector) -> List:
        table_selector = response.css('table.tbl-list')[0]
        table_locator = ContainerListTableLocator()
        table_locator.parse(table=table_selector)
        table = TableExtractor(table_locator=table_locator)
        return_list = []
        for left in table_locator.iter_left_headers():
            container_no_text = table.extract_cell('Ctnr No.', left)
            container_no = self._parse_container_no_from(text=container_no_text)

            mbl_no_text = table.extract_cell('BL no.', left)
            mbl_no = self._parse_mbl_no_from(text=mbl_no_text)

            detail_j_idt_text = table.extract_cell('More detail', left, JidtTdExtractor())
            detail_j_idt = self._parse_detail_j_idt_from(text=detail_j_idt_text)

            history_j_idt_text = table.extract_cell('More History', left, JidtTdExtractor())
            history_j_idt = self._parse_history_j_idt_from(text=history_j_idt_text)

            return_list.append({
                'container_no': container_no,
                'mbl_no': mbl_no,
                'detail_j_idt': detail_j_idt,
                'history_j_idt': history_j_idt,
            })

        return return_list

    def _parse_container_no_from(self, text):
        if not text:
            raise CarrierResponseFormatError('container_no not found')

        m = self._container_patt.match(text)
        if not m:
            raise CarrierResponseFormatError('container_no not match')

        return m.group('container_no')

    def _parse_mbl_no_from(self, text):
        if not text:
            raise CarrierResponseFormatError('mbl_no not found')

        m = self._container_patt.match(text)
        if not m:
            raise CarrierResponseFormatError('mbl_no not match')

        return m.group('container_no')

    def _parse_detail_j_idt_from(self, text: str) -> str:
        if not text:
            return ''

        m = self._j_idt_patt.search(text)
        if not m:
            raise CarrierResponseFormatError('detail_j_idt not match')

        return m.group('j_idt')

    def _parse_history_j_idt_from(self, text: str) -> str:
        if not text:
            return ''

        m = self._j_idt_patt.search(text)
        if not m:
            raise CarrierResponseFormatError('History_j_idt not match')

        return m.group('j_idt')

    @staticmethod
    def extract_date_information(response) -> Dict:
        pattern = re.compile(r'^(?P<vessel>[^/]+) / (?P<voyage>[^/]+)$')

        match_rule = NameOnTableMatchRule(name='2. Departure Date / Arrival Date Information')

        table_selector = find_selector_from(selectors=response.css('table.tbl-list'), rule=match_rule)

        if table_selector is None:
            raise CarrierResponseFormatError(reason='data information table not found')

        location_table_locator = LocationLeftTableLocator()
        location_table_locator.parse(table=table_selector)
        location_table = TableExtractor(table_locator=location_table_locator)

        date_table_locator = DateLeftTableLocator()
        date_table_locator.parse(table=table_selector)
        date_table = TableExtractor(table_locator=date_table_locator)

        un_lo_code_index = 0
        vessel_voyage_index = 1
        date_index = 0

        pol_vessel_voyage = location_table.extract_cell(top=vessel_voyage_index, left='Loading Port')
        pol_m = pattern.match(pol_vessel_voyage)
        pol_vessel = pol_m.group('vessel')
        pol_voyage = pol_m.group('voyage')

        pod_vessel_voyage = location_table.extract_cell(top=vessel_voyage_index, left='Discharging Port')
        pod_m = pattern.match(pod_vessel_voyage)
        pod_vessel = pod_m.group('vessel')
        pod_voyage = pod_m.group('voyage')

        return {
            'pol_un_lo_code': location_table.extract_cell(top=un_lo_code_index, left='Loading Port'),
            'pod_un_lo_code': location_table.extract_cell(top=un_lo_code_index, left='Discharging Port'),
            'pol_vessel': pol_vessel,
            'pol_voyage': pol_voyage,
            'pod_vessel': pod_vessel,
            'pod_voyage': pod_voyage,
            'pod_eta': date_table.extract_cell(top=date_index, left='Arrival Date'),
            'pol_etd': date_table.extract_cell(top=date_index, left='Departure Date'),
        }

    @staticmethod
    def extract_container_status(response) -> List:
        table_selector = response.css('table.tbl-list')

        if not table_selector:
            raise CarrierResponseFormatError(reason='container status table not found')

        table_locator = ContainerStatusTableLocator()
        table_locator.parse(table=table_selector)
        table = TableExtractor(table_locator=table_locator)

        return_list = []
        for left in table_locator.iter_left_headers():
            description = table.extract_cell(top='Status Name', left=left, extractor=DescriptionTdExtractor())
            local_date_time = table.extract_cell(top='Ctnr Date', left=left, extractor=LocalDateTimeTdExtractor())
            location_name = table.extract_cell(top='Ctnr Depot Name', left=left, extractor=LocationNameTdExtractor())

            return_list.append({
                'local_date_time': local_date_time,
                'description': description,
                'location_name': location_name,
            })

        return return_list

    @staticmethod
    def get_mbl_no_set_from(container_list: List):
        mbl_no_list = [container['mbl_no'] for container in container_list]
        mbl_no_set = set(mbl_no_list)

        return mbl_no_set


class BookingRoutingRule(BaseRoutingRule):
    name = 'BOOKING'

    def __init__(self):
        self._search_type = SHIPMENT_TYPE_BOOKING
        self._container_patt = re.compile(r'^(?P<container_no>\w+)')
        self.driver = WhlcContentGetter()

    @classmethod
    def build_request_option(cls, search_nos, task_ids):
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=f'https://google.com',
            meta={
                'search_nos': search_nos,
                'task_ids': task_ids,
            },
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.html'

    def handle(self, response):
        task_ids = response.meta['task_ids']
        search_nos = response.meta['search_nos']
        asyncio.get_event_loop().run_until_complete(self.driver.launch_and_go())
        page_source = asyncio.get_event_loop().run_until_complete(
            self.driver.multi_search(search_nos=search_nos, search_type=self._search_type)
        )

        response_selector = Selector(text=page_source)
        if self.is_search_no_invalid(response=response_selector):
            raise CarrierInvalidSearchNoError(search_type=self._search_type)
        booking_list = self.extract_booking_list(response_selector)
        book_no_set = self.get_book_no_set_from(booking_list=booking_list)

        for task_id, search_no in zip(task_ids, search_nos):
            if search_no not in book_no_set:
                yield ExportErrorData(task_id=task_id, booking_no=search_no, status=CARRIER_RESULT_STATUS_ERROR,
                                      detail='Data was not found')

        for b_idx in range(len(booking_list)):
            search_no = booking_list[b_idx]['booking_no']
            index = search_nos.index(search_no)
            task_id = task_ids[index]
            try:
                page_source = asyncio.get_event_loop().run_until_complete(
                    self.driver.go_detail_page(b_idx + 2)
                )
            except TimeoutError:
                yield ExportErrorData(task_id=task_id, booking_no=search_no, status=CARRIER_RESULT_STATUS_ERROR,
                                      detail='Load detail page timeout')
                self.driver.close_page_and_switch_last()
                continue
            for item in self.handle_booking_detail_page(response=page_source, task_id=task_id, search_no=search_no):
                yield item

            for item in self.handle_booking_history_page(response=page_source, task_id=task_id, search_no=search_no):
                yield item

            self.driver.close_page_and_switch_last()
        self.driver.close()

    def handle_booking_detail_page(self, response, task_id, search_no):
        basic_info = self.extract_basic_info(Selector(text=response))
        vessel_info = self.extract_vessel_info(Selector(text=response))

        yield MblItem(
            task_id=task_id,
            booking_no=search_no,
        )

        yield VesselItem(
            task_id=task_id,
            vessel_key=f"{basic_info['vessel']} / {basic_info['voyage']}",
            vessel=basic_info['vessel'],
            voyage=basic_info['voyage'],
            pol=LocationItem(name=vessel_info['pol']),
            etd=vessel_info['etd'],
        )

        yield VesselItem(
            task_id=task_id,
            vessel_key=f"{basic_info['vessel']} / {basic_info['voyage']}",
            vessel=basic_info['vessel'],
            voyage=basic_info['voyage'],
            pod=LocationItem(name=vessel_info['pod']),
            eta=vessel_info['eta'],
        )

    def handle_booking_history_page(self, response, task_id, search_no):
        container_nos = self.extract_container_no_and_status_links(Selector(text=response))

        for idx in range(len(container_nos)):
            container_no = container_nos[idx]
            # history page
            try:
                page_source = asyncio.get_event_loop().run_until_complete(
                    self.driver.go_booking_history_page(idx + 2)
                )
            except TimeoutError:
                yield ExportErrorData(task_id=task_id, booking_no=search_no, status=CARRIER_RESULT_STATUS_ERROR,
                                      detail='Load status page timeout')
                self.driver.close_page_and_switch_last()
                continue
            history_selector = Selector(text=page_source)

            event_list = self.extract_container_status(response=history_selector)
            container_status_items = self.make_container_status_items(task_id, container_no, event_list)

            yield ContainerItem(
                task_id=task_id,
                container_key=container_no,
                container_no=container_no,
            )

            for item in container_status_items:
                yield item

            self.driver.close_page_and_switch_last()

    @staticmethod
    def is_search_no_invalid(response):
        if response.css('input#q_ref_no1'):
            return True
        return False

    def extract_booking_list(self, response: scrapy.Selector) -> List:
        table_selector = response.css('table.tbl-list')[0]
        table_locator = ContainerListTableLocator()
        table_locator.parse(table=table_selector)
        table = TableExtractor(table_locator=table_locator)
        return_list = []
        for left in table_locator.iter_left_headers():
            booking_no_text = table.extract_cell('Book No.', left)
            booking_no = self._parse_booking_no_from(text=booking_no_text)

            detail_j_idt_text = table.extract_cell('More detail', left, JidtTdExtractor())
            detail_j_idt = self._parse_detail_j_idt_from(text=detail_j_idt_text)

            return_list.append({
                'booking_no': booking_no,
                'detail_j_idt': detail_j_idt,
            })

        return return_list

    def _parse_booking_no_from(self, text):
        if not text:
            raise CarrierResponseFormatError('booking_no not found')

        booking_patt = re.compile(r'^(?P<booking_no>\w+)')
        m = booking_patt.match(text)
        if not m:
            raise CarrierResponseFormatError('booking_no not match')

        return m.group('booking_no')

    def _parse_detail_j_idt_from(self, text: str) -> str:
        if not text:
            return ''

        j_idt_patt = re.compile(r"'(?P<j_idt>j_idt[^,]+)':'(?P=j_idt)'")
        m = j_idt_patt.search(text)
        if not m:
            raise CarrierResponseFormatError('detail_j_idt not match')

        return m.group('j_idt')

    @staticmethod
    def get_book_no_set_from(booking_list: List):
        book_no_list = [booking['booking_no'] for booking in booking_list]
        book_no_set = set(book_no_list)
        return book_no_set

    @staticmethod
    def extract_basic_info(response: scrapy.Selector):
        tables = response.css('table.tbl-list')
        table = tables[0]

        table_locator = BookingBasicTableLocator()
        table_locator.parse(table=table)

        return {
            'vessel': table_locator.get_cell('Vessel Name'),
            'voyage': table_locator.get_cell('Voyage'),
        }

    @staticmethod
    def extract_vessel_info(response: scrapy.Selector):
        tables = response.css('table.tbl-list')
        table = tables[1]

        table_locator = BookingVesselTableLocator()
        table_locator.parse(table=table)

        return {
            'por': table_locator.get_cell('Place of Receipt').replace(u'\xa0', u' '),
            'pol': table_locator.get_cell('Port of Loading').replace(u'\xa0', u' '),
            'pod': table_locator.get_cell('Port of Discharge').replace(u'\xa0', u' '),
            'place_of_deliv': table_locator.get_cell('Place of Delivery').replace(u'\xa0', u' '),
            'eta': table_locator.get_cell('Estimated Departure Date'),
            'etd': table_locator.get_cell('Estimated Arrival Date'),
        }

    @staticmethod
    def extract_container_no_and_status_links(response: scrapy.Selector) -> List:
        tables = response.css('table.tbl-list')
        table = tables[-1]

        table_locator = BookingContainerListTableLocator()
        table_locator.parse(table=table)

        return table_locator.get_container_no_list()

    @classmethod
    def make_container_status_items(cls, task_id, container_no, event_list):
        container_statuses = []
        for container_status in event_list:
            container_statuses.append(
                ContainerStatusItem(
                    task_id=task_id,
                    container_key=container_no,
                    local_date_time=container_status['local_date_time'],
                    description=container_status['description'],
                    location=LocationItem(name=container_status['location_name']),
                )
            )
        return container_statuses

    @staticmethod
    def extract_container_status(response) -> List:
        table_selector = response.css('table.tbl-list')

        if not table_selector:
            raise CarrierResponseFormatError(reason='container status table not found')

        table_locator = ContainerStatusTableLocator()
        table_locator.parse(table=table_selector)
        table = TableExtractor(table_locator=table_locator)

        return_list = []
        for left in table_locator.iter_left_headers():
            description = table.extract_cell(top='Status Name', left=left, extractor=DescriptionTdExtractor())
            local_date_time = table.extract_cell(top='Ctnr Date', left=left, extractor=LocalDateTimeTdExtractor())
            location_name = table.extract_cell(top='Ctnr Depot Name', left=left, extractor=LocationNameTdExtractor())

            return_list.append(
                {
                    'local_date_time': local_date_time,
                    'description': description,
                    'location_name': location_name,
                }
            )

        return return_list


class WhlcContentGetter:
    def __init__(self):
        logging.disable(logging.DEBUG)
        self._type_select_num_map = {
            SHIPMENT_TYPE_MBL: "2",
            SHIPMENT_TYPE_BOOKING: "4",
        }
        self._browser = None
        self._page = None

    async def launch_and_go(self):
        browser_args = [
            "--no-sandbox",
            "--disable-gpu",
            "--disable-blink-features",
            "--disable-infobars",
            "--window-size=1920,1080",
        ]
        self._browser = await launch(headless=True, args=browser_args)
        await self.switch_to_last()
        await self._page.goto(WHLC_BASE_URL, options={"timeout": 60000})
        await asyncio.sleep(3)
        await self._page.screenshot({'path': 'out.png'})
        print('_page: ', await self._page.content())

    async def multi_search(self, search_nos, search_type):
        select_num = self._type_select_num_map[search_type]
        await self._page.waitForSelector("#cargoType")
        await self._page.select("#cargoType", select_num)
        await asyncio.sleep(1)
        for i, search_no in enumerate(search_nos, start=1):
            await self._page.type(f"#q_ref_no{i}", search_no)
            await asyncio.sleep(0.5)
        await asyncio.sleep(3)
        await self._page.click('#Query')
        await asyncio.sleep(3)
        await self.switch_to_last()
        await self._page.waitForSelector("table.tbl-list")
        await asyncio.sleep(5)
        return await self._page.content()

    async def go_detail_page(self, idx: int):
        await self._page.waitForSelector(f'#cargoTrackListBean > table > tbody > tr:nth-child({idx}) > td:nth-child(1) > u')
        await self._page.click(f'#cargoTrackListBean > table > tbody > tr:nth-child({idx}) > td:nth-child(1) > u')
        await asyncio.sleep(3)
        await self.switch_to_last()
        await self._page.waitForSelector("table.tbl-list")
        await asyncio.sleep(3)
        return await self._page.content()

    async def go_history_page(self, idx: int):
        await self._page.waitForSelector(f'#cargoTrackListBean > table > tbody > tr:nth-child({idx}) > td:nth-child(11) > u'),
        await self._page.click(f'#cargoTrackListBean > table > tbody > tr:nth-child({idx}) > td:nth-child(11) > u'),
        await asyncio.sleep(3),
        await self.switch_to_last()
        await self._page.waitForSelector("table.tbl-list")
        await asyncio.sleep(3)
        return await self._page.content()

    async def go_booking_history_page(self, idx: int):
        await self._page.waitForSelector(
                f"#cargoTrackListBean > table > tbody > tr:nth-child({idx}) > td:nth-child(2) > a"),
        await self._page.click(f"#cargoTrackListBean > table > tbody > tr:nth-child({idx}) > td:nth-child(2) > a"),
        await asyncio.sleep(3),
        await self.switch_to_last()
        await self._page.waitForSelector("table.tbl-list")
        await asyncio.sleep(3)
        return await self._page.content()

    async def switch_to_last(self):
        pages = await self._browser.pages()
        self._page = pages[-1]
        await self._page.setUserAgent(
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.71 Safari/537.36")
        await self._page.setViewport(
            {
                'width': 1920,
                'height': 1080,
                'deviceScaleFactor': 1,
            }
        )
        await asyncio.sleep(1)

    async def get_page_source(self):
        return await self._page.content()

    async def close_page(self):
        await self._page.close()
        await asyncio.sleep(1)

    async def close(self):
        await self._browser.close()

    def close_page_and_switch_last(self):
        asyncio.get_event_loop().run_until_complete(self.close_page())
        asyncio.get_event_loop().run_until_complete(self.switch_to_last())


class BookingBasicTableLocator(BaseTableLocator):
    def __init__(self):
        self._td_map = {}

    def parse(self, table: Selector, numbers: int = 1):
        tr_list = table.css('tbody tr')

        for tr in tr_list:
            # the value will be emtpy
            titles = tr.css('th')
            values = tr.css('td')

            for i in range(len(titles)):
                title = titles[i].css('strong::text').get().strip()
                value = (values[i].css('::text').get() or '').strip()
                self._td_map[title] = value

    def get_cell(self, top, left=None) -> Selector:
        return self._td_map[top]

    def has_header(self, top=None, left=None) -> bool:
        pass


class BookingVesselTableLocator(BaseTableLocator):

    def __init__(self):
        self._td_map = {}

    def parse(self, table: Selector, numbers: int = 1):
        tr_list = table.css('tbody tr')

        for tr in tr_list:
            # the value will be emtpy
            titles = tr.css('th')
            values = tr.css('td')

            for i in range(len(titles)):
                title = titles[i].css('strong::text').get().strip()
                value = (values[i].css('::text').get() or '').strip()
                self._td_map[title] = value

    def get_cell(self, top, left=None) -> Selector:
        return self._td_map[top]

    def has_header(self, top=None, left=None) -> bool:
        pass


class BookingContainerListTableLocator(BaseTableLocator):

    TR_TITLE_INDEX = 0
    TR_DATA_BEGIN_INDEX = 1

    def __init__(self):
        self._td_map = []
        self._data_len = 0

    def parse(self, table: Selector):
        title_tr = table.css('tbody tr')[self.TR_TITLE_INDEX]
        data_tr_list = table.css('tbody tr')[self.TR_DATA_BEGIN_INDEX:]

        title_text_list = title_tr.css('th strong::text').getall()
        title_text_list[0] = 'ID'

        for data_tr in data_tr_list:
            if len(data_tr.css('td')) == 1:
                break
            row = {}
            for title_index, title_text in enumerate(title_text_list):
                title_text = title_text.strip()
                container_no = data_tr.css('td a::text').get().strip()
                tds = data_tr.css('td')
                row[title_text] = (tds[title_index].css('::text').get() or '').strip()
                if title_text == 'Ctnr No.':
                    row[title_text] = container_no

            self._td_map.append(row)

    def get_container_no_list(self) -> List:
        return [row['Ctnr No.'] for row in self._td_map]

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


class ContainerListTableLocator(BaseTableLocator):
    TR_TITLE_INDEX = 0
    TR_DATA_BEGIN_INDEX = 1

    def __init__(self):
        self._td_map = {}
        self._data_len = 0

    def parse(self, table: Selector):
        title_tr = table.css('tr')[self.TR_TITLE_INDEX]
        data_tr_list = table.css('tr')[self.TR_DATA_BEGIN_INDEX:]

        title_text_list = title_tr.css('th::text').getall()

        for title_index, title_text in enumerate(title_text_list):
            data_index = title_index

            title_text = title_text.strip()
            self._td_map[title_text] = []

            for data_tr in data_tr_list:
                data_td = data_tr.css('td')[data_index]

                self._td_map[title_text].append(data_td)

        first_title_text = title_text_list[0]
        self._data_len = len(self._td_map[first_title_text])

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


class LocationLeftTableLocator(BaseTableLocator):
    """
        +------------------------------------------------+ <tbody>
        | Title 1 | Data 1  | Data 2 | Title    | Data   | <tr>
        +---------+---------+--------+----------+--------+
        | Title 2 |         |        | Title    | Data   | <tr>
        +---------+---------+--------+----------+--------+ </tbody>
        (       only use here        )
    """

    TR_TITLE_INDEX_BEGIN = 1
    TH_TITLE_INDEX = 0
    TD_DATA_INDEX_BEGIN = 0
    TD_DATA_INDEX_END = 2

    def __init__(self):
        self._td_map = {}
        self._left_header_set = set()

    def parse(self, table: Selector):
        top_index_set = set()
        tr_list = table.css('tr')[self.TR_TITLE_INDEX_BEGIN:]

        for tr in tr_list:
            left_header = tr.css('th::text')[self.TH_TITLE_INDEX].get().strip()
            self._left_header_set.add(left_header)

            data_td_list = tr.css('td')[self.TD_DATA_INDEX_BEGIN:self.TD_DATA_INDEX_END]
            for top_index, td in enumerate(data_td_list):
                top_index_set.add(top_index)
                td_dict = self._td_map.setdefault(top_index, {})
                td_dict[left_header] = td

    def get_cell(self, top, left) -> Selector:
        try:
            return self._td_map[top][left]
        except KeyError as err:
            raise HeaderMismatchError(repr(err))

    def has_header(self, top=None, left=None) -> bool:
        return (top is None) and (left in self._left_header_set)


class DateLeftTableLocator(BaseTableLocator):
    """
        +------------------------------------------------+ <tbody>
        | Title   | Data    | Data   | Title 1  | Data   | <tr>
        +---------+---------+--------+----------+--------+
        | Title   |         |        | Title 2  | Data   | <tr>
        +---------+---------+--------+----------+--------+ </tbody>
                                     (   only use here   )
    """

    TR_TITLE_INDEX_BEGIN = 1
    TH_TITLE_INDEX = 1
    TD_DATA_INDEX_BEGIN = 2
    TD_DATA_INDEX_END = 3

    def __init__(self):
        self._td_map = {}
        self._left_header_set = set()

    def parse(self, table: Selector):
        top_index_set = set()
        tr_list = table.css('tr')[self.TR_TITLE_INDEX_BEGIN:]

        for tr in tr_list:
            left_header = tr.css('th::text')[self.TH_TITLE_INDEX].get().strip()
            self._left_header_set.add(left_header)

            data_td_list = tr.css('td')[self.TD_DATA_INDEX_BEGIN:self.TD_DATA_INDEX_END]
            for top_index, td in enumerate(data_td_list):
                top_index_set.add(top_index)
                td_dict = self._td_map.setdefault(top_index, {})
                td_dict[left_header] = td

    def get_cell(self, top, left) -> Selector:
        try:
            return self._td_map[top][left]
        except KeyError as err:
            raise HeaderMismatchError(repr(err))

    def has_header(self, top=None, left=None) -> bool:
        return (top is None) and (left in self._left_header_set)


class ContainerStatusTableLocator(BaseTableLocator):
    """
        +-----------------------------------+ <tbody>
        | Title 1 | Title 2 | ... | Title N | <tr>
        +---------+---------+-----+---------+
        | Data    |         |     |         | <tr>
        +---------+---------+-----+---------+
        | Data    |         |     |         | <tr>
        +---------+---------+-----+---------+
        | ...     |         |     |         | <tr>
        +---------+---------+-----+---------+
        | Data    |         |     |         | <tr>
        +---------+---------+-----+---------+ </tbody>
    """

    TR_TITLE_INDEX = 0
    TR_DATA_BEGIN_INDEX = 1

    def __init__(self):
        self._td_map = {}
        self._data_len = 0

    def parse(self, table: Selector):
        title_tr = table.css('tr')[self.TR_TITLE_INDEX]
        data_tr_list = table.css('tr')[self.TR_DATA_BEGIN_INDEX:]

        title_text_list = title_tr.css('th::text').getall()

        for title_index, title_text in enumerate(title_text_list):
            data_index = title_index

            title_text = title_text.strip()
            self._td_map[title_text] = []

            for data_tr in data_tr_list:
                data_td = data_tr.css('td')[data_index]

                self._td_map[title_text].append(data_td)

        self._data_len = len(data_tr_list)

    def get_cell(self, top, left) -> Selector:
        try:
            return self._td_map[top][left]
        except KeyError as err:
            raise HeaderMismatchError(repr(err))

    def has_header(self, top=None, left=None) -> bool:
        return (top in self._td_map) and (left is None)

    def iter_left_headers(self):
        for index in range(self._data_len):
            yield index


class DescriptionTdExtractor(BaseTableCellExtractor):
    def extract(self, cell: Selector) -> str:
        td_text = cell.css('::text').get()
        td_text = td_text.replace('\\n', '')
        td_text = ' '.join(td_text.split())
        return td_text.strip()


class LocalDateTimeTdExtractor(BaseTableCellExtractor):
    def extract(self, cell: Selector) -> str:
        td_text = cell.css('::text').get()
        td_text = td_text.replace('\\n', '')
        return td_text.strip()


class LocationNameTdExtractor(BaseTableCellExtractor):
    def extract(self, cell: Selector) -> str:
        td_text = cell.css('::text').get()
        td_text = td_text.replace('\\n', '')
        td_text = td_text.replace('\\t', '')
        return td_text.strip()


class NameOnTableMatchRule(BaseMatchRule):
    TABLE_NAME_QUERY = 'tr td a::text'

    def __init__(self, name: str):
        self.name = name

    def check(self, selector: scrapy.Selector) -> bool:
        table_name = selector.css(self.TABLE_NAME_QUERY).get()

        if not isinstance(table_name, str):
            return False

        return table_name.strip() == self.name

class JidtTdExtractor(BaseTableCellExtractor):

    def extract(self, cell: Selector):
        j_idt_text = cell.css('u a::attr(onclick)').get()
        return j_idt_text