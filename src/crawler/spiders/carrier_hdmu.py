import dataclasses
from typing import List, Dict

from scrapy import Selector, Request, FormRequest
from twisted.python.failure import Failure

from crawler.core_carrier.base_spiders import BaseCarrierSpider, CARRIER_DEFAULT_SETTINGS
from crawler.core_carrier.exceptions import (
    CarrierInvalidMblNoError, CarrierResponseFormatError, SuspiciousOperationError)
from crawler.core_carrier.items import (
    MblItem, LocationItem, VesselItem, ContainerItem, ContainerStatusItem, BaseCarrierItem, DebugItem)
from crawler.core_carrier.request_helpers import ProxyManager, RequestOption, ProxyMaxRetryError
from crawler.core_carrier.rules import BaseRoutingRule, RuleManager
from crawler.extractors.selector_finder import CssQueryTextStartswithMatchRule, find_selector_from
from crawler.extractors.table_cell_extractors import BaseTableCellExtractor, FirstTextTdExtractor
from crawler.extractors.table_extractors import (
    TableExtractor, TopHeaderTableLocator, TopLeftHeaderTableLocator, LeftHeaderTableLocator)

BASE_URL = 'https://www.hmm21.com'


@dataclasses.dataclass
class ForceRestart:
    pass


class RequestQueue:

    def __init__(self):
        self._queue = []

    def clear(self):
        self._queue.clear()

    def add(self, request: Request):
        self._queue.append(request)

    def is_empty(self):
        return not bool(self._queue)

    def next(self):
        return self._queue.pop(0)


# item_name
MBL = 'MBL'
VESSEL = 'VESSEL'
CONTAINER = 'CONTAINER'
CONTAINER_STATUS = 'CONTAINER_STATUS'
AVAILABILITY = 'AVAILABILITY'


class ItemRecorder:
    def __init__(self):
        self._record = set()  # (key1, key2, ...)
        self._items = []

    def record_item(self, key, item: BaseCarrierItem = None, items: List[BaseCarrierItem] = None):
        self._record.add(key)

        if item:
            self._items.append(item)

        if items:
            self._items.extend(items)

    def is_item_recorded(self, key):
        return key in self._record

    @property
    def items(self):
        return self._items


class CarrierHdmuSpider(BaseCarrierSpider):
    name = 'carrier_hdmu'
    custom_settings = {
        **CARRIER_DEFAULT_SETTINGS,
        'DOWNLOAD_TIMEOUT': 30,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._cookiejar_id = 0
        self._item_recorder = ItemRecorder()

        rules = [
            CookiesRoutingRule(),
            MainRoutingRule(self._item_recorder),
            ContainerRoutingRule(self._item_recorder),
            AvailabilityRoutingRule(self._item_recorder),
        ]

        self._request_queue = RequestQueue()
        self._rule_manager = RuleManager(rules=rules)
        self._proxy_manager = ProxyManager(session='hdmu', logger=self.logger)

    def start(self):
        if self.mbl_no.startswith('HDMU'):
            self.mbl_no = self.mbl_no[4:]

        yield self._prepare_restart()

    def retry(self, failure: Failure):
        try:
            yield self._prepare_restart()
        except ProxyMaxRetryError as err:
            for item in self._item_recorder.items:
                yield item
            yield err.build_error_data()

    def parse(self, response):
        yield DebugItem(info={'meta': dict(response.meta)})

        routing_rule = self._rule_manager.get_rule_by_response(response=response)

        # save file
        save_name = routing_rule.get_save_name(response=response)
        self._saver.save(to=save_name, text=response.text)

        # handle
        for result in routing_rule.handle(response=response):
            if isinstance(result, RequestOption):
                rule_proxy_option = self._proxy_manager.apply_proxy_to_request_option(option=result)
                rule_proxy_cookie_option = self._add_cookiejar_id_into_request_option(option=rule_proxy_option)
                rule_request = self._build_request_by(option=rule_proxy_cookie_option)
                self._request_queue.add(request=rule_request)
            elif isinstance(result, ForceRestart):
                try:
                    restart_request = self._prepare_restart()
                    self._request_queue.add(request=restart_request)
                except ProxyMaxRetryError as err:
                    error_item = err.build_error_data()
                    self._item_recorder.record_item(key=('ERROR', None), item=error_item)
            elif isinstance(result, BaseCarrierItem):
                pass
            else:
                raise RuntimeError()

        # yield request / item
        if not self._request_queue.is_empty():
            yield self._request_queue.next()
        else:
            for item in self._item_recorder.items:
                yield item

    def _prepare_restart(self) -> Request:
        self._request_queue.clear()
        self._proxy_manager.renew_proxy()
        self._cookiejar_id += 1

        option = CookiesRoutingRule.build_request_option(mbl_no=self.mbl_no, cookiejar_id=self._cookiejar_id)
        restart_proxy_option = self._proxy_manager.apply_proxy_to_request_option(option=option)
        restart_proxy_cookie_option = self._add_cookiejar_id_into_request_option(option=restart_proxy_option)
        return self._build_request_by(option=restart_proxy_cookie_option)

    def _add_cookiejar_id_into_request_option(self, option) -> RequestOption:
        return option.copy_and_extend_by(meta={'cookiejar': self._cookiejar_id})

    def _build_request_by(self, option: RequestOption):
        meta = {
            RuleManager.META_CARRIER_CORE_RULE_NAME: option.rule_name,
            **option.meta,
        }

        if option.method == RequestOption.METHOD_GET:
            return Request(
                url=option.url,
                headers=option.headers,
                meta=meta,
                dont_filter=True,
                callback=self.parse,
                errback=self.retry,
            )

        elif option.method == RequestOption.METHOD_POST_FORM:
            return FormRequest(
                url=option.url,
                headers=option.headers,
                formdata=option.form_data,
                meta=meta,
                dont_filter=True,
                callback=self.parse,
                errback=self.retry,
            )

        elif option.method == RequestOption.METHOD_POST_BODY:
            return Request(
                method='POST',
                url=option.url,
                headers=option.headers,
                body=option.body,
                meta=meta,
                dont_filter=True,
                callback=self.parse,
                errback=self.retry,
            )

        else:
            raise SuspiciousOperationError(msg=f'Unexpected request method: `{option.method}`')


# -------------------------------------------------------------------------------


class CookiesRoutingRule(BaseRoutingRule):
    name = 'COOKIES'

    @classmethod
    def build_request_option(cls, mbl_no, cookiejar_id: int):
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            # url=f'{BASE_URL}/cms/company/engn/index.jsp',
            url=BASE_URL,
            headers={
                'Host': 'www.hmm21.com',
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
            },
            meta={
                'mbl_no': mbl_no,
                'cookiejar': cookiejar_id,
            },
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.html'

    def handle(self, response):
        mbl_no = response.meta['mbl_no']

        if self._require_cookies_exists(response=response):
            yield MainRoutingRule.build_request_option(mbl_no=mbl_no)
        else:
            yield ForceRestart()

    @staticmethod
    def _require_cookies_exists(response):
        cookies = {}
        for cookie_byte in response.headers.getlist('Set-Cookie'):
            kv = cookie_byte.decode('utf-8').split(';')[0].split('=')
            cookies[kv[0]] = kv[1]

        # return 'ak_bmsc' in cookies
        return cookies


# -------------------------------------------------------------------------------


class MainRoutingRule(BaseRoutingRule):
    name = 'MAIN'

    def __init__(self, item_recorder: ItemRecorder):
        self._item_recorder = item_recorder

    @classmethod
    def build_request_option(cls, mbl_no):
        form_data = {
            'number': mbl_no,
            'type': '1',
            'selectedContainerIndex': '',
            'blFields': '3',
            'cnFields': '3',
            'is_quick': 'Y',
            'numbers': [
                mbl_no, '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '',
            ],
        }

        body = encode_urlencoded_body_from(form_data=form_data)

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_POST_BODY,
            url=f'{BASE_URL}/_/ebiz/track_trace/trackCTP_nTmp.jsp',
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'Host': 'www.hmm21.com',
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
            },
            body=body,
            meta={
                'mbl_no': mbl_no,
            },
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.html'

    def handle(self, response):
        mbl_no = response.meta['mbl_no']

        self._check_mbl_no(response=response)

        if not self._item_recorder.is_item_recorded(key=(MBL, mbl_no)):
            tracking_results = self._extract_tracking_results(response=response)
            customs_status = self._extract_customs_status(response=response)
            cargo_delivery_info = self._extract_cargo_delivery_info(response=response)
            latest_update = self._extract_lastest_update(response=response)

            mbl_item = MblItem(
                mbl_no=mbl_no,
                por=LocationItem(name=tracking_results['location.por']),
                pod=LocationItem(name=tracking_results['location.pod']),
                pol=LocationItem(name=tracking_results['location.pol']),
                final_dest=LocationItem(name=tracking_results['Location.dest']),
                por_atd=tracking_results['departure.por_actual'],
                ata=tracking_results['arrival.pod_actual'],
                eta=tracking_results['arrival.pod_estimate'],
                atd=tracking_results['departure.pol_actual'],
                etd=tracking_results['departure.pol_estimate'],
                us_ams_status=customs_status['us_ams'],
                ca_aci_status=customs_status['canada_aci'],
                eu_ens_status=customs_status['eu_ens'],
                cn_cams_status=customs_status['china_cams'],
                ja_afr_status=customs_status['japan_afr'],
                freight_status=cargo_delivery_info['freight_status'],
                us_customs_status=cargo_delivery_info['us_customs_status'],
                deliv_order=cargo_delivery_info['delivery_order_status'],
                latest_update=latest_update,
                deliv_ata=cargo_delivery_info['delivery_order_time'],
                pol_ata=tracking_results['arrival.pol_actual'],
                firms_code=cargo_delivery_info['firm_code'],
                freight_date=cargo_delivery_info['freight_time'],
                us_customs_date=cargo_delivery_info['us_customs_time'],
                bl_type=cargo_delivery_info['bl_type'],
                way_bill_status=cargo_delivery_info['way_bill_status'],
                way_bill_date=cargo_delivery_info['way_bill_time'],
            )
            self._item_recorder.record_item(key=(MBL, mbl_no), item=mbl_item)

        if not self._item_recorder.is_item_recorded(key=(VESSEL, mbl_no)):
            vessel = self._extract_vessel(response=response)

            vessel_item = VesselItem(
                vessel_key=vessel['vessel'],
                vessel=vessel['vessel'],
                voyage=vessel['voyage'],
                pol=LocationItem(name=vessel['pol']),
                pod=LocationItem(name=vessel['pod']),
                ata=vessel['ata'],
                eta=vessel['eta'],
                atd=vessel['atd'],
                etd=vessel['etd'],
            )
            self._item_recorder.record_item(key=(VESSEL, mbl_no), item=vessel_item)

        # parse other containers if there are many containers
        container_contents = self._extract_container_contents(response=response)
        h_num = -1
        for container_content in container_contents:
            if all([
                    self._item_recorder.is_item_recorded(key=(CONTAINER, container_content.container_no)),
                    self._item_recorder.is_item_recorded(key=(AVAILABILITY, container_content.container_no)),
            ]):
                continue

            elif container_content.is_current:
                response.meta['container_index'] = container_content.index

                container_routing_rule = ContainerRoutingRule(self._item_recorder)
                for result in container_routing_rule.handle(response=response):
                    yield result

            else:
                h_num -= 1
                yield ContainerRoutingRule.build_request_option(
                    mbl_no=mbl_no, container_index=container_content.index, h_num=h_num)

        # avoid this function not yield anything
        yield MblItem()

    @staticmethod
    def _check_mbl_no(response):
        err_message = response.css('div#trackingForm p.text_type03::text').get()
        if err_message == 'B/L number is invalid.  Please try it again with correct number.':
            raise CarrierInvalidMblNoError()

    @staticmethod
    def _extract_tracking_results(response):
        table_selector = response.css('#trackingForm div.base_table01')[0]
        table_locator = TopLeftHeaderTableLocator()
        table_locator.parse(table=table_selector)
        table = TableExtractor(table_locator=table_locator)
        red_blue_td_extractor = RedBlueTdExtractor()

        return {
            'location.por': table.extract_cell('Origin', 'Location'),
            'location.pol': table.extract_cell('Loading Port', 'Location'),
            'location.pod': table.extract_cell('Discharging Port', 'Location'),
            'Location.dest': table.extract_cell('Destination', 'Location'),
            'arrival.pol_estimate': table.extract_cell('Loading Port', 'Arrival', red_blue_td_extractor)['red'],
            'arrival.pol_actual': table.extract_cell('Loading Port', 'Arrival', red_blue_td_extractor)['blue'],
            'arrival.pod_estimate': table.extract_cell('Discharging Port', 'Arrival', red_blue_td_extractor)['red'],
            'arrival.pod_actual': table.extract_cell('Discharging Port', 'Arrival', red_blue_td_extractor)['blue'],
            'arrival.dest_estimate': table.extract_cell('Destination', 'Arrival', red_blue_td_extractor)['red'],
            'arrival.dest_actual': table.extract_cell('Destination', 'Arrival', red_blue_td_extractor)['blue'],
            'departure.por_estimate': table.extract_cell('Origin', 'Departure', red_blue_td_extractor)['red'],
            'departure.por_actual': table.extract_cell('Origin', 'Departure', red_blue_td_extractor)['blue'],
            'departure.pol_estimate': table.extract_cell('Loading Port', 'Departure', red_blue_td_extractor)['red'],
            'departure.pol_actual': table.extract_cell('Loading Port', 'Departure', red_blue_td_extractor)['blue'],
        }

    @staticmethod
    def _extract_cargo_delivery_info(response):
        table_exist_match_rule = CssQueryTextStartswithMatchRule(
            css_query='::text', startswith='Cargo Delivery Information')
        table_exist = find_selector_from(selectors=response.css('h4'), rule=table_exist_match_rule)

        if not table_exist:
            return {
                'bl_type': None,
                'way_bill_status': None,
                'way_bill_time': None,
                'freight_status': None,
                'freight_time': None,
                'us_customs_status': None,
                'us_customs_time': None,
                'firm_code': None,
                'delivery_order_status': None,
                'delivery_order_time': None,
            }

        table_selector = response.css('#trackingForm div.left_table01')[1]
        table_locator = LeftHeaderTableLocator()
        table_locator.parse(table=table_selector)
        table = TableExtractor(table_locator=table_locator)

        if table.has_header(left='Way Bill'):
            bl_type = 'Way Bill'
            way_bill_status = table.extract_cell(0, 'Way Bill')
            way_bill_time = table.extract_cell(1, 'Way Bill')
        elif table.has_header(left='Original B/L'):
            bl_type = None
            way_bill_status = None
            way_bill_time = None
        else:
            raise CarrierResponseFormatError('Cargo Delivery Information Change!!!')

        return {
            'bl_type': bl_type,
            'way_bill_status': way_bill_status,
            'way_bill_time': way_bill_time,
            'freight_status': table.extract_cell(0, 'Freight'),
            'freight_time': table.extract_cell(1, 'Freight') or None,
            'us_customs_status': table.extract_cell(0, 'US Customs'),
            'us_customs_time': table.extract_cell(1, 'US Customs') or None,
            'firm_code': table.extract_cell(0, 'Firms Code'),
            'delivery_order_status': table.extract_cell(0, 'Delivery Order'),
            'delivery_order_time': table.extract_cell(1, 'Delivery Order') or None,
        }

    @staticmethod
    def _extract_customs_status(response):
        table_selector = response.css('#trackingForm div.base_table01')[4]
        table_locator = TopLeftHeaderTableLocator()
        table_locator.parse(table=table_selector)
        table = TableExtractor(table_locator=table_locator)

        return {
            'us_ams': table.extract_cell('US / AMS', 'Status') or None,
            'canada_aci': table.extract_cell('Canada / ACI', 'Status') or None,
            'eu_ens': table.extract_cell('EU / ENS', 'Status') or None,
            'china_cams': table.extract_cell('China / CAMS', 'Status') or None,
            'japan_afr': table.extract_cell('Japan / AFR', 'Status') or None,
        }

    @staticmethod
    def _extract_lastest_update(response):
        latest_update = ' '.join(response.css('p.text_type02::text')[-1].get().split()[-6:])
        return latest_update

    @staticmethod
    def _extract_vessel(response):
        table_selector = response.css('#trackingForm div.base_table01')[3]
        table_locator = TopHeaderTableLocator()
        table_locator.parse(table=table_selector)
        table = TableExtractor(table_locator=table_locator)
        red_blue_td_extractor = RedBlueTdExtractor()

        vessel_voyage_str = table.extract_cell('Vessel / Voyage', 0).split()
        vessel = ' '.join(vessel_voyage_str[:-1])
        voyage = vessel_voyage_str[-1]

        return {
            'vessel': vessel,
            'voyage': voyage,
            'pol': table.extract_cell('Loading Port', 0),
            'pod': table.extract_cell('Discharging Port', 0),
            'ata': table.extract_cell('Arrival', 0, red_blue_td_extractor)['blue'],
            'eta': table.extract_cell('Arrival', 0, red_blue_td_extractor)['red'],
            'atd': table.extract_cell('Departure', 0, red_blue_td_extractor)['blue'],
            'etd': table.extract_cell('Departure', 0, red_blue_td_extractor)['red'],
        }

    def _extract_container_contents(self, response):
        table_selector = self._get_container_table(response=response)
        container_selectors = table_selector.css('tbody tr')

        container_contents = []
        for index, selector in enumerate(container_selectors):
            container_no = selector.css('a::text').get()
            is_current = bool(selector.css('a[class="redBoldLink"]').get())
            container_contents.append(ContainerContent(
                container_no=container_no,
                index=index,
                is_current=is_current,
            ))
        return container_contents

    @staticmethod
    def _get_container_table(response):
        container_table = response.css('#trackingForm div.base_table01')[1]
        return container_table


# -------------------------------------------------------------------------------


@dataclasses.dataclass
class ContainerContent:
    container_no: str
    index: int
    is_current: bool


class ContainerRoutingRule(BaseRoutingRule):
    name = 'CONTAINER'

    def __init__(self, item_recorder: ItemRecorder):
        self._item_recorder = item_recorder

    @classmethod
    def build_request_option(cls, mbl_no, container_index, h_num):
        form_data = {
            'selectedContainerIndex': f'{container_index}',
            'hNum': f'{h_num}',
            'tempBLOrBKG': mbl_no,
            'numbers': [
                mbl_no, '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '',
            ],
        }
        body = encode_urlencoded_body_from(form_data=form_data)

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_POST_BODY,
            url=f'{BASE_URL}/_/ebiz/track_trace/trackCTP_nTmp.jsp?US_IMPORT=Y&BNO_IMPORT={mbl_no}',
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'Host': 'www.hmm21.com',
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
            },
            body=body,
            meta={
                'mbl_no': mbl_no,
                'container_index': container_index,
            },
        )

    def get_save_name(self, response) -> str:
        container_index = response.meta['container_index']
        return f'{self.name}_{container_index}.html'

    def handle(self, response):
        mbl_no = response.meta['mbl_no']
        container_index = response.meta['container_index']

        container_info = self._extract_container_info(response=response, container_index=container_index)
        container_no = container_info['container_no']

        if not self._item_recorder.is_item_recorded(key=(CONTAINER, container_no)):
            tracking_results = self._extract_tracking_results(response=response)
            empty_return_location = self._extract_empty_return_location(response=response)

            container_item = ContainerItem(
                container_key=container_no,
                container_no=container_no,
                last_free_day=container_info['lfd'],
                mt_location=LocationItem(name=empty_return_location['empty_return_location']),
                det_free_time_exp_date=empty_return_location['fdd'],
                por_etd=tracking_results['departure.por_estimate'],
                pol_eta=tracking_results['arrival.pol_estimate'],
                final_dest_eta=tracking_results['arrival.dest_estimate'],
                ready_for_pick_up=None,
            )
            self._item_recorder.record_item(key=(CONTAINER, container_no), item=container_item)

        if not self._item_recorder.is_item_recorded(key=(CONTAINER_STATUS, container_no)):
            container_status = self._extract_container_status_list(response=response)

            container_status_items = []
            for container in container_status:
                container_no = container_info['container_no']

                container_status_items.append(
                    ContainerStatusItem(
                        container_key=container_no,
                        description=container['status'],
                        local_date_time=container['date'],
                        location=LocationItem(name=container['location']),
                        transport=container['mode'],
                    )
                )

            self._item_recorder.record_item(key=(CONTAINER_STATUS, container_no), items=container_status_items)

        # catch availability
        if not self._item_recorder.is_item_recorded(key=(AVAILABILITY, container_no)):
            ava_exist = self._extract_availability_exist(response=response)
            if ava_exist:
                yield AvailabilityRoutingRule.build_request_option(mbl_no=mbl_no, container_no=container_no)
            else:
                self._item_recorder.record_item(key=(AVAILABILITY, container_no))

        # avoid this function not yield anything
        yield MblItem()

    @staticmethod
    def _extract_tracking_results(response):
        table_selector = response.css('#trackingForm div.base_table01')[0]
        table_locator = TopLeftHeaderTableLocator()
        table_locator.parse(table=table_selector)
        table = TableExtractor(table_locator=table_locator)
        red_blue_td_extractor = RedBlueTdExtractor()

        return {
            'location.por': table.extract_cell('Origin', 'Location'),
            'location.pol': table.extract_cell('Loading Port', 'Location'),
            'location.pod': table.extract_cell('Discharging Port', 'Location'),
            'Location.dest': table.extract_cell('Destination', 'Location'),
            'arrival.pol_estimate': table.extract_cell('Loading Port', 'Arrival', red_blue_td_extractor)['red'],
            'arrival.pol_actual': table.extract_cell('Loading Port', 'Arrival', red_blue_td_extractor)['blue'],
            'arrival.pod_estimate': table.extract_cell('Discharging Port', 'Arrival', red_blue_td_extractor)['red'],
            'arrival.pod_actual': table.extract_cell('Discharging Port', 'Arrival', red_blue_td_extractor)['blue'],
            'arrival.dest_estimate': table.extract_cell('Destination', 'Arrival', red_blue_td_extractor)['red'],
            'arrival.dest_actual': table.extract_cell('Destination', 'Arrival', red_blue_td_extractor)['blue'],
            'departure.por_estimate': table.extract_cell('Origin', 'Departure', red_blue_td_extractor)['red'],
            'departure.por_actual': table.extract_cell('Origin', 'Departure', red_blue_td_extractor)['blue'],
            'departure.pol_estimate': table.extract_cell('Loading Port', 'Departure', red_blue_td_extractor)['red'],
            'departure.pol_actual': table.extract_cell('Loading Port', 'Departure', red_blue_td_extractor)['blue'],
        }

    def _extract_container_info(self, response, container_index):
        table_selector = self._get_container_table(response=response)
        table_locator = TopHeaderTableLocator()
        table_locator.parse(table=table_selector)
        table = TableExtractor(table_locator=table_locator)
        index = container_index

        if table.has_header(top='Last Free Day (Basic)'):
            lfd = table.extract_cell('Last Free Day (Basic)', index)
        else:
            lfd = None

        return {
            'container_no': table.extract_cell('Container No.', index, extractor=FirstTextTdExtractor('a::text')),
            'type/size': table.extract_cell('Cntr Type/Size', index),
            'lfd': lfd,
        }

    @staticmethod
    def _extract_container_status_list(response) -> list:
        table_selector = response.css('#trackingForm div.base_table01')[5]
        table_locator = TopHeaderTableLocator()
        table_locator.parse(table=table_selector)
        table = TableExtractor(table_locator=table_locator)

        container_status_list = []
        for index, tr in enumerate(table_selector.css('tbody tr')):
            date = table.extract_cell('Date', index)
            time = table.extract_cell('Time', index)
            location = table.extract_cell('Location', index, extractor=IgnoreDashTdExtractor())
            mode = table.extract_cell('Mode', index, extractor=IgnoreDashTdExtractor())

            container_status_list.append({
                'date': f'{date} {time}',
                'location': location,
                'status': table.extract_cell('Status Description', index),
                'mode': mode,
            })

        return container_status_list

    @staticmethod
    def _extract_availability_exist(response):
        ava_exist = response.xpath('//a[text()="Container Availability"]').get()
        return bool(ava_exist)

    @staticmethod
    def _extract_empty_return_location(response):
        table_exist_match_rule = CssQueryTextStartswithMatchRule(
            css_query='::text', startswith='Empty Container Return Location')
        table_exist = find_selector_from(selectors=response.css('h4'), rule=table_exist_match_rule)

        if not table_exist:
            return {
                'empty_return_location': None,
                'fdd': None,
            }

        table_selector = response.css('#trackingForm div.left_table01')[-1]
        table_locator = LeftHeaderTableLocator()
        table_locator.parse(table=table_selector)
        table = TableExtractor(table_locator=table_locator)
        fdd = table.extract_cell(0, 'Detention Freetime Expiry Date', extractor=IgnoreDashTdExtractor())

        return {
            'empty_return_location': table.extract_cell(0, 'Empty Container Return Location'),
            'fdd': fdd,
        }

    @staticmethod
    def _get_container_table(response):
        container_table = response.css('#trackingForm div.base_table01')[1]
        return container_table


# -------------------------------------------------------------------------------


class AvailabilityRoutingRule(BaseRoutingRule):
    name = 'AVAILABILITY'

    def __init__(self, item_recorder: ItemRecorder):
        self._item_recorder = item_recorder

    @classmethod
    def build_request_option(cls, mbl_no, container_no):
        form_data = {
            'bno': mbl_no,
            'cntrNo': f'{container_no}',
        }
        body = encode_urlencoded_body_from(form_data=form_data)

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_POST_BODY,
            url=f'{BASE_URL}/_/ebiz/track_trace/WUTInfo.jsp',
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
                'Host': 'www.hmm21.com',
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
            },
            body=body,
            meta={
                'container_no': container_no,
            },
        )

    def get_save_name(self, response) -> str:
        container_no = response.meta['container_no']
        return f'{self.name}_{container_no}.html'

    def handle(self, response):
        container_no = response.meta['container_no']

        ready_for_pick_up = self._extract_availability(response)

        ava_item = ContainerItem(
            container_key=container_no,
            ready_for_pick_up=ready_for_pick_up,
        )
        self._item_recorder.record_item(key=(AVAILABILITY, container_no), item=ava_item)

        return []

    @staticmethod
    def _extract_availability(response):
        table_selector = response.css('table.ty03')
        table_locator = TopHeaderTableLocator()
        table_locator.parse(table=table_selector)
        table = TableExtractor(table_locator=table_locator)
        return table.extract_cell('STATUS', 0) or None


class RedBlueTdExtractor(BaseTableCellExtractor):

    def extract(self, cell: Selector):
        red_text_list = [c.strip() for c in cell.css('span.font_red::text').getall()]
        blue_text_list = [c.strip() for c in cell.css('span.font_blue::text').getall()]
        return {
            'red': ' '.join(red_text_list) or None,
            'blue': ' '.join(blue_text_list) or None,
        }


class IgnoreDashTdExtractor(BaseTableCellExtractor):
    def extract(self, cell: Selector):
        td_text = cell.css('::text').get()
        text = td_text.strip() if td_text else ''
        return text if text != '-' else None


# -------------------------------------------------------------------------------


def encode_urlencoded_body_from(form_data: Dict) -> str:
    urlencoded_body_with_and = ''
    for k, v in form_data.items():
        if isinstance(v, list):
            for v_i in v:
                urlencoded_body_with_and += f'{k}={v_i}&'

        urlencoded_body_with_and += f'{k}={v}&'
    urlencoded_body = urlencoded_body_with_and[:-1]

    return urlencoded_body

