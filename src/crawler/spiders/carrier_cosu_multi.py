import time
import random
from typing import List, Dict

import scrapy
from scrapy import Selector
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib3.exceptions import ReadTimeoutError

from crawler.core_carrier.base import SHIPMENT_TYPE_MBL, SHIPMENT_TYPE_BOOKING, CARRIER_RESULT_STATUS_ERROR
from crawler.core_carrier.exceptions import SuspiciousOperationError, LoadWebsiteTimeOutFatal, CarrierInvalidMblNoError, \
    CarrierInvalidSearchNoError
from crawler.core_carrier.items import (
    LocationItem,
    MblItem,
    VesselItem,
    ContainerStatusItem,
    ContainerItem,
    BaseCarrierItem,
    DebugItem,
    ExportErrorData,
)
from crawler.core_carrier.base_spiders import BaseMultiCarrierSpider
from crawler.core_carrier.request_helpers import RequestOption
from crawler.core_carrier.rules import BaseRoutingRule, RuleManager
from crawler.extractors.selector_finder import CssQueryExistMatchRule, find_selector_from
from crawler.extractors.table_cell_extractors import FirstTextTdExtractor, BaseTableCellExtractor
from crawler.extractors.table_extractors import BaseTableLocator, HeaderMismatchError, TableExtractor


class CarrierCosuSpider(BaseMultiCarrierSpider):
    name = 'carrier_cosu_multi'

    def __init__(self, *args, **kwargs):
        super(CarrierCosuSpider, self).__init__(*args, **kwargs)

        bill_rules = [
            MainInfoRoutingRule(),
        ]

        booking_rules = [
            BookingInfoRoutingRule(),
        ]

        if self.search_type == SHIPMENT_TYPE_MBL:
            self._rule_manager = RuleManager(rules=bill_rules)
        elif self.search_type == SHIPMENT_TYPE_BOOKING:
            self._rule_manager = RuleManager(rules=booking_rules)

    def start(self):
        if self.search_type == SHIPMENT_TYPE_MBL:
            option = MainInfoRoutingRule.build_request_option(mbl_nos=self.search_nos, task_ids=self.task_ids)
            yield self._build_request_by(option=option)
        else:
            # option = BookingInfoRoutingRule.build_request_option(booking_nos=[self.booking_no], task_id=t_id)
            option = BookingInfoRoutingRule.build_request_option(booking_nos=self.booking_nos, task_ids=self.task_ids)
            yield self._build_request_by(option=option)

    def parse(self, response):
        yield DebugItem(info={'meta': dict(response.meta)})

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
        meta = {RuleManager.META_CARRIER_CORE_RULE_NAME: option.rule_name, **option.meta}

        if option.method == RequestOption.METHOD_GET:
            return scrapy.Request(
                method=option.method,
                headers=option.headers,
                url=option.url,
                meta=meta,
                dont_filter=True,
            )
        else:
            raise SuspiciousOperationError(msg=f'Unexpected request method: `{option.method}`')


# ---------------------------------------------------------------------------------------------------------


class MainInfoRoutingRule(BaseRoutingRule):
    name = 'MAIN_INFO'

    def __init__(self):
        pass

    @classmethod
    def build_request_option(cls, mbl_nos, task_ids) -> RequestOption:
        url = f'https://www.google.com'

        return RequestOption(
            method=RequestOption.METHOD_GET,
            rule_name=cls.name,
            url=url,
            meta={
                'mbl_nos': mbl_nos,
                'task_ids': task_ids,
            },
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.html'

    def handle(self, response):
        mbl_nos = response.meta['mbl_nos']
        task_ids = response.meta['task_ids']
        content_getter = ContentGetter()

        for mbl_no, task_id in zip(mbl_nos, task_ids):
            response_text = content_getter.search_and_return(search_no=mbl_no, is_booking=False)
            response_selector = scrapy.Selector(text=response_text)

            raw_booking_nos = response_selector.css('a.exitedBKNumber::text').getall()
            booking_nos = [raw_booking_no.strip() for raw_booking_no in raw_booking_nos]

            if self._is_mbl_no_invalid(response=response_selector) and not booking_nos:
                yield ExportErrorData(task_id=task_id, mbl_no=mbl_no, status=CARRIER_RESULT_STATUS_ERROR,
                                      detail='Data was not found')
            elif not self._is_mbl_no_invalid(response=response_selector):
                item_extractor = ItemExtractor(task_id=task_id)
                for item in item_extractor.extract(
                        response=response_selector, content_getter=content_getter, search_type=SHIPMENT_TYPE_MBL):
                    yield item
            elif booking_nos:
                for booking_no in booking_nos:
                    yield MblItem(task_id=task_id, mbl_no=mbl_no)
                    for b_item in self.process_booking(content_getter=content_getter, booking_no=booking_no, task_id=task_id):
                        yield b_item

        content_getter.close()

    @staticmethod
    def _is_mbl_no_invalid(response: Selector) -> bool:
        return bool(response.css('div.noFoundTips'))

    def process_booking(self, content_getter, booking_no: str, task_id: int):
        item_extractor = ItemExtractor(task_id=task_id)
        response_text = content_getter.search_and_return(search_no=booking_no, is_booking=True)
        response_selector = scrapy.Selector(text=response_text)
        if self._is_booking_no_invalid(response=response_selector):
            yield ExportErrorData(task_id=task_id, booking_no=booking_no, status=CARRIER_RESULT_STATUS_ERROR,
                                  detail='Data was not found')

        for item in item_extractor.extract(
                response=response_selector,
                content_getter=content_getter,
                search_type=SHIPMENT_TYPE_BOOKING,
        ):
            yield item

    @staticmethod
    def _is_booking_no_invalid(response: Selector) -> bool:
        return bool(response.css('div.noFoundTips'))

# ---------------------------------------------------------------------------------------------------------


class BookingInfoRoutingRule(BaseRoutingRule):
    name = 'BOOKING_INFO'

    @classmethod
    def build_request_option(cls, task_ids: str, booking_nos: str) -> RequestOption:
        url = f'https://www.google.com'

        return RequestOption(
            method=RequestOption.METHOD_GET,
            rule_name=cls.name,
            url=url,
            meta={
                'booking_nos': booking_nos,
                'task_ids': task_ids,
            },
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.html'

    def handle(self, response):
        task_ids = response.meta['task_ids']
        booking_nos = response.meta['booking_nos']
        content_getter = ContentGetter()

        for booking_no, task_id in zip(booking_nos, task_ids):
            response_text = content_getter.search_and_return(search_no=booking_no, is_booking=True)
            response_selector = scrapy.Selector(text=response_text)

            if self._is_booking_no_invalid(response=response_selector):
                yield ExportErrorData(task_id=task_id, booking_no=booking_no, status=CARRIER_RESULT_STATUS_ERROR,
                                      detail='Data was not found')
                continue

            item_extractor = ItemExtractor(task_id=task_id)
            for item in item_extractor.extract(
                response=response_selector,
                content_getter=content_getter,
                search_type=SHIPMENT_TYPE_BOOKING,
            ):
                yield item

        content_getter.close()

    @staticmethod
    def _is_booking_no_invalid(response: Selector) -> bool:
        return bool(response.css('div.noFoundTips'))


# ---------------------------------------------------------------------------------------------------------


class ItemExtractor:
    def __init__(self, task_id):
        self.task_id = task_id

    def extract(self, response: scrapy.Selector, content_getter, search_type) -> BaseCarrierItem:
        mbl_item = self._make_main_item(response=response, search_type=search_type, task_id=self.task_id)
        vessel_items = self._make_vessel_items(response=response, task_id=self.task_id)
        container_items = self._make_container_items(response=response, task_id=self.task_id)

        for item in vessel_items + [mbl_item]:
            yield item

        content_getter.scroll_to_bottom_of_page()
        for c_i, c_item in enumerate(container_items):
            response_text = content_getter.click_container_status_button(c_i)
            response_selector = scrapy.Selector(text=response_text)

            container_status_items = self._make_container_status_items(
                task_id=self.task_id,
                container_no=c_item['container_no'],
                response=response_selector,
            )

            for item in container_status_items + [c_item]:
                yield item

    @classmethod
    def _make_main_item(cls, response: scrapy.Selector, search_type, task_id) -> BaseCarrierItem:
        mbl_data = cls._extract_main_info(response=response)
        mbl_item = MblItem(
            task_id=task_id,
            vessel=mbl_data.get('vessel', None),
            voyage=mbl_data.get('voyage', None),
            por=LocationItem(name=mbl_data.get('por_name', None)),
            pol=LocationItem(name=mbl_data.get('pol_name', None)),
            pod=LocationItem(
                name=mbl_data.get('pod_name', None),
                firms_code=mbl_data.get('pod_firms_code', None),
            ),
            final_dest=LocationItem(
                name=mbl_data.get('final_dest_name', None),
                firms_code=mbl_data.get('final_dest_firms_code', None),
            ),
            etd=mbl_data.get('etd', None),
            atd=mbl_data.get('atd', None),
            eta=mbl_data.get('eta', None),
            ata=mbl_data.get('ata', None),
            deliv_eta=mbl_data.get('pick_up_eta', None),
            bl_type=mbl_data.get('bl_type', None),
            cargo_cutoff_date=mbl_data.get('cargo_cutoff', None),
            surrendered_status=mbl_data.get('surrendered_status', None),
            # trans_eta=data.get('trans_eta', None),
            # container_quantity=data.get('container_quantity', None),
        )
        if mbl_data['mbl_no'] and search_type == SHIPMENT_TYPE_MBL:
            mbl_item['mbl_no'] = mbl_data['mbl_no']
        elif search_type == SHIPMENT_TYPE_BOOKING:
            mbl_item['booking_no'] = mbl_data['booking_no']

        return mbl_item

    @staticmethod
    def _extract_main_info(response: scrapy.Selector) -> Dict:
        table_like_div = response.css('div.ivu-c-detailPart')[0]  # 0 for booking info bookmark, 1 for print bookmark
        table_locator = LeftHeadDivTableLocator()
        table_locator.parse(table=table_like_div)
        table_extractor = TableExtractor(table_locator=table_locator)

        vessel_voyage = table_extractor.extract_cell(left='Vessel / Voyage', top=None)
        raw_vessel, raw_voyage = vessel_voyage.split('/')
        vessel, voyage = raw_vessel.strip(), raw_voyage.strip()

        raw_booking_no = table_extractor.extract_cell(left='Booking Number', top=None)
        booking_no = raw_booking_no.split(' ')[0]

        if table_extractor.has_header(left='POD Firms Code'):
            pod_firms_code = table_extractor.extract_cell(left='POD Firms Code', top=None)
        else:
            pod_firms_code = None

        if table_extractor.has_header(left='Final Destination Firms Code'):
            final_dest_firms_code = table_extractor.extract_cell(left='Final Destination Firms Code', top=None)
        else:
            final_dest_firms_code = None

        if table_extractor.has_header(left='BL Surrendered Status'):
            surrendered_status = table_extractor.extract_cell(left='BL Surrendered Status', top=None)
        else:
            surrendered_status = None

        if table_extractor.has_header(left='B/L Type'):
            bl_type = table_extractor.extract_cell(left='B/L Type', top=None)
        else:
            bl_type = None

        data = {
            'mbl_no': table_extractor.extract_cell(left='Bill of Lading Number', top=None),
            'booking_no': booking_no,
            'por_name': table_extractor.extract_cell(left='Place of Receipt', top=None),
            'pol_name': table_extractor.extract_cell(left='POL', top=None),
            'pod_name': table_extractor.extract_cell(left='POD', top=None),
            'final_dest_name': table_extractor.extract_cell(left='Final Destination', top=None),
            'vessel': vessel,
            'voyage': voyage or None,
            'bl_type': bl_type,
            'pick_up_eta': table_extractor.extract_cell(left='ETA at Place of Delivery', top=None),
            'cargo_cutoff': table_extractor.extract_cell(left='Cargo Cutoff', top=None),
            'pod_firms_code': pod_firms_code,
            'final_dest_firms_code': final_dest_firms_code,
            'surrendered_status': surrendered_status,
        }

        vessel_schedule_div = response.css('div.ivu-steps-horizontal')
        xtd_div = vessel_schedule_div.css('div.ivu-steps-item-pol')
        xta_div = vessel_schedule_div.css('div.ivu-steps-item-pod')

        xtd_key = xtd_div.css('div.ivu-steps-name::text').get().strip()
        xtd_time = xtd_div.css('div.ivu-steps-date::text').get().strip()

        if xtd_key == 'ATD':
            data['atd'] = xtd_time
            data['etd'] = None
        else:
            data['atd'] = None
            data['etd'] = xtd_time

        xta_key = xta_div.css('div.ivu-steps-name::text').get().strip()
        xta_time = xta_div.css('div.ivu-steps-date::text').get()

        # xta_time might be None
        if xta_time:
            xta_time.strip()

        if xta_key == 'ATA':
            data['ata'] = xta_time
            data['eta'] = None
        else:
            data['ata'] = None
            data['eta'] = xta_time

        return data

    @classmethod
    def _make_vessel_items(cls, response: scrapy.Selector, task_id) -> List[BaseCarrierItem]:
        vessel_data = cls._extract_schedule_detail_info(response=response)
        vessels = []
        for vessel in vessel_data:
            vessels.append(
                VesselItem(
                    task_id=task_id,
                    vessel_key=vessel['vessel'],
                    vessel=vessel['vessel'],
                    voyage=vessel['voyage'],
                    pol=LocationItem(name=vessel['pol']),
                    pod=LocationItem(name=vessel['pod']),
                    etd=vessel['etd'],
                    eta=vessel['eta'],
                    atd=vessel['atd'],
                    ata=vessel['ata'],
                )
            )
        return vessels

    @staticmethod
    def _extract_schedule_detail_info(response: scrapy.Selector) -> List:
        # 0 for booking info bookmark, 1 for print bookmark
        table_like_div = response.css('div.cargoTrackingSailing div.ivu-table')[0]
        table_locator = TopHeadDivTableLocator()
        table_locator.parse(table=table_like_div)
        table_extractor = TableExtractor(table_locator=table_locator)

        vessels = []
        for left in table_locator.iter_left_index():
            service_voyage = table_extractor.extract_cell(
                top='Service / Voyage', left=left, extractor=LabelContentTableCellExtractor()
            )

            departure_date = table_extractor.extract_cell(
                top='Departure Date', left=left, extractor=LabelContentTableCellExtractor()
            )

            arrive_date = table_extractor.extract_cell(
                top='Arrival Date', left=left, extractor=LabelContentTableCellExtractor()
            )

            vessels.append(
                {
                    'vessel_key': table_extractor.extract_cell(
                        top='Vessel', left=left, extractor=FirstTextTdExtractor(css_query='a::text')
                    ),
                    'vessel': table_extractor.extract_cell(
                        top='Vessel', left=left, extractor=FirstTextTdExtractor(css_query='a::text')
                    ),
                    'voyage': service_voyage['Voyage'],
                    'pol': table_extractor.extract_cell(
                        top='POL', left=left, extractor=FirstTextTdExtractor(css_query='span::text')
                    ),
                    'pod': table_extractor.extract_cell(
                        top='POD', left=left, extractor=FirstTextTdExtractor(css_query='span::text')
                    ),
                    'etd': departure_date['expected'],
                    'atd': departure_date['actual'],
                    'eta': arrive_date['expected'],
                    'ata': arrive_date['actual'],
                }
            )

        return vessels

    @classmethod
    def _make_container_items(cls, response: scrapy.Selector, task_id) -> List[BaseCarrierItem]:
        container_infos = cls._extract_container_infos(response=response)

        container_items = []
        for container_info in container_infos:
            container_items.append(
                ContainerItem(
                    task_id=task_id,
                    container_key=container_info['container_key'],
                    container_no=container_info['container_no'],
                    last_free_day=container_info['last_free_day'],
                    depot_last_free_day=container_info['depot_last_free_day'],
                )
            )
        return container_items

    @staticmethod
    def _extract_container_infos(response: scrapy.Selector):
        table_like_div = response.css('div.movingList')[0]  # 0 for booking info bookmark, 1 for print bookmark
        table_locator = TopHeadDivTableLocator()
        table_locator.parse(table=table_like_div)
        table_extractor = TableExtractor(table_locator=table_locator)
        container_infos = []

        for left in table_locator.iter_left_index():
            container_no = table_extractor.extract_cell(
                top='Container No.', left=left, extractor=OnlyContentTableCellExtractor()
            )[
                0
            ]  # 0 container_no, 1 container_spec
            lfd_related = {}
            if table_extractor.has_header(top='LFD'):
                lfd_related = table_extractor.extract_cell(
                    top='LFD', left=left, extractor=LabelContentTableCellExtractor()
                )

            container_infos.append(
                {
                    'container_key': get_container_key(container_no=container_no),
                    'container_no': container_no,
                    'last_free_day': lfd_related.get('LFD', ''),
                    'depot_last_free_day': lfd_related.get('Depot LFD', ''),
                }
            )

        return container_infos

    @classmethod
    def _make_container_status_items(cls, task_id: str, container_no: str, response: scrapy.Selector) -> List[BaseCarrierItem]:
        container_status_infos = cls._extract_container_status_infos(response=response)

        container_status_items = []
        for container_status_info in container_status_infos:
            container_status_items.append(
                ContainerStatusItem(
                    task_id=task_id,
                    container_key=get_container_key(container_no),
                    description=container_status_info['description'],
                    local_date_time=container_status_info['local_date_time'],
                    location=LocationItem(name=container_status_info['location']),
                    transport=container_status_info['transport'],
                )
            )

        return container_status_items

    @staticmethod
    def _extract_container_status_infos(response: scrapy.Selector):
        pop_up_divs = response.css('div.ivu-poptip-content')
        rule = CssQueryExistMatchRule(css_query='p.poptip-title-up')
        container_status_div = find_selector_from(selectors=pop_up_divs, rule=rule)

        table_like_div = container_status_div.css('div.ivu-table')
        table_locator = TopHeadDivTableLocator()
        table_locator.parse(table=table_like_div)
        table_extractor = TableExtractor(table_locator=table_locator)

        container_status_infos = []
        for left in table_locator.iter_left_index():
            multi_status = table_extractor.extract_cell(
                top='Latest Status', left=left, extractor=OnlyContentTableCellExtractor()
            )  # 0 description, 1 time, 2 transport

            container_status_infos.append(
                {
                    'description': multi_status[0],
                    'local_date_time': multi_status[1],
                    'transport': multi_status[2],
                    'location': table_extractor.extract_cell(
                        top='Location', left=left, extractor=JoinAllWithSpaceTableCellExtractor()
                    ),
                }
            )

        return container_status_infos


class LeftHeadDivTableLocator(BaseTableLocator):
    def __init__(self):
        self._td_map = {}  # title: data_td

    def parse(self, table: Selector):
        label_cells = table.css('div.label p.tebleCell')
        content_cells = table.css('div.content p.tebleCell')

        for label_cell, content_cell in zip(label_cells, content_cells):
            raw_label_texts = label_cell.css('::text').getall()
            label_with_colon = ''.join([raw_label_t.strip() for raw_label_t in raw_label_texts])
            label = label_with_colon[:-1]  # delete colon

            raw_content_texts = content_cell.css('::text').getall()
            content = ''.join([raw_content_t.strip() for raw_content_t in raw_content_texts])

            data_td = Selector(text=f'<td>{content}</td>')

            self._td_map[label] = data_td

    def get_cell(self, left: str, top=None) -> Selector:
        assert top is None
        try:
            return self._td_map[left]
        except KeyError as err:
            raise HeaderMismatchError(repr(err))

    def has_header(self, left=None, top=None) -> bool:
        assert top is None
        return left in self._td_map


class TopHeadDivTableLocator(BaseTableLocator):
    def __init__(self):
        self._td_map = {}  # title: td

    def parse(self, table: Selector):
        ths = table.css('div.ivu-table-header th')
        ths_span_text = [th.css('span::text').get() for th in ths]
        trs = table.css('tr.ivu-table-row')

        for tr in trs:
            tds = tr.css('td')
            for th_span_text, td in zip(ths_span_text, tds):
                self._td_map.setdefault(th_span_text, [])
                self._td_map[th_span_text].append(td)

    def get_cell(self, top, left) -> Selector:
        try:
            return self._td_map[top][left]
        except (KeyError, IndexError) as err:
            raise HeaderMismatchError(repr(err))

    def has_header(self, top=None, left=None) -> bool:
        assert left is None
        return bool(top in self._td_map)

    def iter_left_index(self):
        keys = list(self._td_map.keys())
        if not keys:
            return 0

        first_tds = self._td_map[keys[0]]
        for i in range(len(first_tds)):
            yield i


class LabelContentTableCellExtractor(BaseTableCellExtractor):
    def extract(self, cell: Selector):
        result = {}
        info_items = cell.css('p.infoItem')

        for info_item in info_items:
            label_with_colon = info_item.css('span.label::text').get().strip()
            label = label_with_colon[:-1]

            raw_content = info_item.css('span.content::text').get()
            content = raw_content.strip() if raw_content else raw_content

            result[label] = content

        return result


class JoinAllWithSpaceTableCellExtractor(BaseTableCellExtractor):
    def extract(self, cell: Selector):
        all_texts = cell.css('::text').getall()
        result_text = ' '.join([text.strip() for text in all_texts]).strip()

        return result_text


class OnlyContentTableCellExtractor(BaseTableCellExtractor):
    def extract(self, cell: Selector):
        results = []
        info_items = cell.css('p.infoItem')

        for info_item in info_items:
            raw_content = info_item.css('span.content::text').get()
            content = raw_content.strip() if raw_content else raw_content
            results.append(content)

        return results


# ---------------------------------------------------------------------------------------------------------


class ContentGetter:
    def __init__(self):
        options = webdriver.FirefoxOptions()
        # options.add_argument('--headless')
        options.add_argument(f'user-agent={self._random_choose_user_agent()}')
        self._driver = webdriver.Firefox(firefox_options=options, service_log_path='/dev/null')
        self._driver.get('https://elines.coscoshipping.com/ebusiness/cargoTracking')
        self._is_first = True

    def close(self):
        self._driver.close()

    def search_and_return(self, search_no: str, is_booking: bool = True):

        if self._is_first:
            self._is_first = False
            self._handle_cookie()

        if is_booking:
            trackingType = 'BOOKING'
        else:
            trackingType = 'BILLOFLADING'

        self._driver.get(
            f'https://elines.coscoshipping.com/ebusiness/cargoTracking?trackingType={trackingType}&number={search_no}'
        )

        try:
            time.sleep(10)
            return self._driver.page_source
        except TimeoutException:
            raise LoadWebsiteTimeOutFatal()

    def _handle_cookie(self):
        try:
            accept_btn = WebDriverWait(self._driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[class='ivu-btn ivu-btn-primary ivu-btn-large']"))
            )
        except (TimeoutException, ReadTimeoutError):
            raise LoadWebsiteTimeOutFatal()

        # accept cookie
        time.sleep(1)
        accept_btn.click()
        time.sleep(1)

    def click_container_status_button(self, idx: int):
        repeat_three_times_buttons = self._driver.find_elements_by_css_selector(
            "i[class='ivu-icon ivu-icon-ios-information']"
        )
        button = repeat_three_times_buttons[idx]

        button.click()
        time.sleep(8)
        return self._driver.page_source

    def scroll_to_bottom_of_page(self):
        self._driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)

    @staticmethod
    def _random_choose_user_agent():
        user_agents = [
            # firefox
            ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:80.0) ' 'Gecko/20100101 ' 'Firefox/80.0'),
            ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:79.0) ' 'Gecko/20100101 ' 'Firefox/79.0'),
            ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:78.0) ' 'Gecko/20100101 ' 'Firefox/78.0'),
            ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:78.0.1) ' 'Gecko/20100101 ' 'Firefox/78.0.1'),
        ]

        return random.choice(user_agents)


def get_container_key(container_no: str):
    container_key = container_no[:10]

    # if len(container_key) != 10:
    #     raise CarrierResponseFormatError(f'Invalid container_no `{container_no}`')

    return container_key
