import dataclasses
from typing import Callable

import scrapy
from scrapy import Selector

from crawler.core_carrier.base import CARRIER_RESULT_STATUS_FATAL
from crawler.core_carrier.base_spiders import BaseCarrierSpider
from crawler.core_carrier.exceptions import CarrierInvalidMblNoError, CarrierResponseFormatError, BaseCarrierError
from crawler.core_carrier.items import MblItem, LocationItem, VesselItem, ContainerItem, ContainerStatusItem, \
    ExportErrorData, BaseCarrierItem
from crawler.core_carrier.rules import BaseRoutingRule, RoutingRequest, RuleManager
from crawler.extractors.table_cell_extractors import BaseTableCellExtractor, FirstTextTdExtractor
from crawler.extractors.table_extractors import (
    TableExtractor, TopHeaderTableLocator, TopLeftHeaderTableLocator, LeftHeaderTableLocator)
from w3lib.http import basic_auth_header
import random


BASE_URL = 'https://www.hmm21.com'


class CarrierHdmuSpider(BaseCarrierSpider):
    name = 'carrier_hdmu'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        rules = [
            CookiesRoutingRule(),
            MainRoutingRule(),
            ContainerRoutingRule(),
            AvailabilityRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)

    def start_requests(self):
        routing_request = CookiesRoutingRule.build_routing_request(
            mbl_no=self.mbl_no, proxy_auth=get_new_proxy_auth(), callback=self.parse)
        yield self._rule_manager.build_request_by(routing_request=routing_request)

    def parse(self, response):
        routing_rule = self._rule_manager.get_rule_by_response(response=response)

        save_name = routing_rule.get_save_name(response=response)
        self._saver.save(to=save_name, text=response.text)

        for result in routing_rule.handle(response=response):
            if isinstance(result, BaseCarrierItem):
                yield result
            elif isinstance(result, RoutingRequest):
                yield self._rule_manager.build_request_by(routing_request=result)
            else:
                raise RuntimeError()

# -------------------------------------------------------------------------------


def get_new_proxy_auth():
    return basic_auth_header(
        f'groups-RESIDENTIAL,session-rand{random.random()}',
        'XZTBLpciyyTCFb3378xWJbuYY',
    )


class CarrierProxyMaxRetryError(BaseCarrierError):
    status = CARRIER_RESULT_STATUS_FATAL

    def build_error_data(self):
        return ExportErrorData(status=self.status, detail='<proxy-max-retry-error>')


class CookiesRoutingRule(BaseRoutingRule):
    name = 'COOKIES'
    MAX_RETRY = 10

    def __init__(self):
        self._retry_count = 0

    @staticmethod
    def build_request(proxy_auth, callback: Callable, dont_filter: bool = False) -> scrapy.Request:
        return scrapy.Request(
            url='https://www.hmm21.com',
            headers={
                'Upgrade-Insecure-Requests': '1',
                'Proxy-Authorization': proxy_auth,
            },
            meta={'proxy': 'proxy.apify.com:8000', 'proxy_auth': proxy_auth, 'callback': callback},
            dont_filter=dont_filter,
            callback=callback,
            errback=CookiesRoutingRule.retry,
        )

    @staticmethod
    def build_routing_request(mbl_no, proxy_auth, callback: Callable, dont_filter: bool = False) -> RoutingRequest:
        request = CookiesRoutingRule.build_request(proxy_auth=proxy_auth, callback=callback, dont_filter=dont_filter)
        request.meta['mbl_no'] = mbl_no
        request.meta['retry_count'] = 0
        return RoutingRequest(request=request, rule_name=CookiesRoutingRule.name)

    @classmethod
    def retry(cls, response):
        retry_count = response.meta['retry_count']
        callback = response.meta['callback']

        if retry_count < cls.MAX_RETRY:
            request = cls.build_request(proxy_auth=get_new_proxy_auth(), callback=callback, dont_filter=True)
            request.meta['retry_count'] = retry_count + 1
            yield request
        else:
            raise CarrierProxyMaxRetryError()

    def get_save_name(self, response) -> str:
        retry_count = response.meta['retry_count']
        return f'{self.name}_{retry_count}.html'

    def handle(self, response):
        mbl_no = response.meta['mbl_no']
        callback = response.meta['callback']
        proxy_auth = response.meta['proxy_auth']

        cookies = self.handle_cookies(response=response)

        if not cookies:
            for request in self.retry(response=response):
                yield RoutingRequest(request=request, rule_name=CookiesRoutingRule.name)
        else:
            yield MainRoutingRule.build_routing_request(mbl_no=mbl_no, proxy_auth=proxy_auth, callback=callback)

    @staticmethod
    def handle_cookies(response):
        cookies = {}
        for cookie_byte in response.headers.getlist('Set-Cookie'):
            kv = cookie_byte.decode('utf-8').split(';')[0].split('=')
            cookies[kv[0]] = kv[1]

        return cookies


class MainRoutingRule(BaseRoutingRule):
    name = 'MAIN'

    @staticmethod
    def build_routing_request(mbl_no, proxy_auth, callback: Callable) -> RoutingRequest:
        formdata = {
            'number': mbl_no,
            'type': '1',
            'selectedContainerIndex': '',
            'blFields': '3',
            'cnFields': '3',
            'is_quick': 'Y',
            'numbers': [
                mbl_no,
                '', '', '', '', '',
                '', '', '', '', '',
                '', '', '', '', '',
                '', '', '', '', '',
                '', '', '',
            ],
        }

        request = scrapy.FormRequest(
            url='https://www.hmm21.com/ebiz/track_trace/trackCTP_nTmp.jsp',
            headers={
                'Upgrade-Insecure-Requests': '1',
                'Proxy-Authorization': proxy_auth,
            },
            formdata=formdata,
            meta={'proxy': 'proxy.apify.com:8000', 'mbl_no': mbl_no, 'callback': callback},
            dont_filter=True,
            callback=callback,
            errback=CookiesRoutingRule.retry,
        )

        return RoutingRequest(request=request, rule_name=MainRoutingRule.name)

    def get_save_name(self, response) -> str:
        return f'{self.name}.html'

    def handle(self, response):
        mbl_no = response.meta['mbl_no']
        callback = response.meta['callback']

        self._check_mbl_no(response=response)

        tracking_results = self._extract_tracking_results(response=response)
        customs_status = self._extract_customs_status(response=response)
        cargo_delivery_info = self._extract_cargo_delivery_info(response=response)
        latest_update = self._extract_lastest_update(response=response)

        yield MblItem(
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

        vessel = self._extract_vessel(response=response)
        yield VesselItem(
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

        # parse other containers if there are many containers
        container_contents = self._extract_container_contents(response=response)
        h_num = -1
        for container_content in container_contents:
            if container_content.is_current:
                response.meta['container_index'] = container_content.index
                response.meta['mbl_no'] = mbl_no

                container_routing_rule = ContainerRoutingRule()
                for item in container_routing_rule.handle(response=response):
                    yield item

            else:
                h_num -= 1
                ContainerRoutingRule.build_routing_request(
                    mbl_no=mbl_no, container_index=container_content.index, h_num=h_num, callback=callback)

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


@dataclasses.dataclass
class ContainerContent:
    container_no: str
    index: int
    is_current: bool


class ContainerRoutingRule(BaseRoutingRule):
    name = 'CONTAINER'

    @classmethod
    def build_routing_request(cls, mbl_no, container_index, h_num, callback) -> RoutingRequest:
        url = f'{BASE_URL}/ebiz/track_trace/trackCTP_nTmp.jsp?US_IMPORT=Y&BNO_IMPORT={mbl_no}'
        form_data = {
            'selectedContainerIndex': f'{container_index}',
            'hNum': f'{h_num}',
            'tempBLOrBKG': mbl_no,
            'numbers': [
                mbl_no,
                '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '',
            ],
        }
        request = scrapy.FormRequest(
            url=url,
            formdata=form_data,
            meta={'container_index': container_index, 'mbl_no': mbl_no, 'callback': callback},
            callback=callback,
            errback=CookiesRoutingRule.retry,
        )
        return RoutingRequest(request=request, rule_name=cls.name)

    def get_save_name(self, response) -> str:
        container_index = response.meta['container_index']
        return f'{self.name}_{container_index}'

    def handle(self, response):
        mbl_no = response.meta['mbl_no']
        container_index = response.meta['container_index']
        callback=response.meta['callback']

        tracking_results = self._extract_tracking_results(response=response)
        container_info = self._extract_container_info(response=response, container_index=container_index)
        empty_return_location = self._extract_empty_return_location(response=response)
        container_status = self._extract_container_status_list(response=response)

        container_no = container_info['container_no']

        yield ContainerItem(
            container_key=container_no,
            container_no=container_no,
            last_free_day=container_info['lfd'],
            mt_location=LocationItem(name=empty_return_location['empty_return_location']),
            det_free_time_exp_date=empty_return_location['fdd'],
            por_etd=tracking_results['departure.por_estimate'],
            pol_eta=tracking_results['arrival.pol_estimate'],
            final_dest_eta=tracking_results['arrival.dest_estimate'],
            ready_for_pick_up=None,  # it may be assign in availability
        )

        # catch availability
        ava_exist = self._extract_availability_exist(response=response)
        if ava_exist:
            AvailabilityRoutingRule.build_routing_request(mbl_no=mbl_no, container_no=container_no, callback=callback)

        for container in container_status:
            container_no = container_info['container_no']

            yield ContainerStatusItem(
                container_key=container_no,
                description=container['status'],
                local_date_time=container['date'],
                location=LocationItem(name=container['location']),
                transport=container['mode']
            )

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
        table_selector = response.css('#trackingForm div.left_table01')[2]
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


class AvailabilityRoutingRule(BaseRoutingRule):
    name = 'AVAILABILITY'

    @classmethod
    def build_routing_request(cls, mbl_no, container_no, callback) -> RoutingRequest:
        url = f'{BASE_URL}/ebiz/track_trace/WUTInfo.jsp'
        form_data = {
            'bno': mbl_no,
            'cntrNo': f'{container_no}',
        }
        request = scrapy.FormRequest(
            url=url,
            formdata=form_data,
            meta={'container_no': container_no},
            callback=callback,
            errback=CookiesRoutingRule.retry,
        )
        return RoutingRequest(request=request, rule_name=cls.name)

    def get_save_name(self, response) -> str:
        container_no = response.meta['container_no']
        return f'{self.name}_{container_no}'

    def handle(self, response):
        container_no = response.meta['container_no']

        ready_for_pick_up = self._extract_availability(response)

        yield ContainerItem(
            container_key=container_no,
            ready_for_pick_up=ready_for_pick_up,
        )

    @staticmethod
    def _extract_availability(response):
        table_selector = response.css('table.ty03')
        table_locator = TopHeaderTableLocator()
        table_locator.parse(table=table_selector)
        table = TableExtractor(table_locator=table_locator)
        return table.extract_cell('STATUS', 0)


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

