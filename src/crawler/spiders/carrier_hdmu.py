import dataclasses
import json
from typing import List, Dict
from urllib.parse import urlencode

from scrapy import Selector, Request, FormRequest
from twisted.python.failure import Failure

from crawler.core_carrier.base import SHIPMENT_TYPE_MBL, SHIPMENT_TYPE_BOOKING
from crawler.core_carrier.base_spiders import BaseCarrierSpider, CARRIER_DEFAULT_SETTINGS
from crawler.core_carrier.exceptions import (
    CarrierResponseFormatError, SuspiciousOperationError, CarrierInvalidMblNoError,
    CarrierInvalidSearchNoError)
from crawler.core_carrier.items import (
    MblItem,
    LocationItem,
    VesselItem,
    ContainerItem,
    ContainerStatusItem,
    BaseCarrierItem,
    DebugItem,
)
from crawler.core_carrier.request_helpers import ProxyManager, RequestOption, ProxyMaxRetryError
from crawler.core_carrier.rules import BaseRoutingRule, RuleManager
from crawler.extractors.selector_finder import CssQueryTextStartswithMatchRule, find_selector_from, BaseMatchRule
from crawler.extractors.table_cell_extractors import BaseTableCellExtractor, FirstTextTdExtractor
from crawler.core.table import (
    TableExtractor,
    BaseTable,
)

BASE_URL = 'http://www.hmm21.com'
# item_name
MBL = 'MBL'
VESSEL = 'VESSEL'
CONTAINER = 'CONTAINER'
CONTAINER_STATUS = 'CONTAINER_STATUS'
AVAILABILITY = 'AVAILABILITY'


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


class CookieHelper:
    @staticmethod
    def get_cookies(response):
        cookies = {}
        for cookie_byte in response.headers.getlist('Set-Cookie'):
            kv = cookie_byte.decode('utf-8').split(';')[0].split('=')
            cookies[kv[0]] = kv[1]

        return cookies

    @staticmethod
    def get_cookie_str(cookies: Dict):
        cookies_str = ''
        for key, value in cookies.items():
            cookies_str += f'{key}={value}; '

        return cookies_str


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


# -------------------------------------------------------------------------------


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

        bill_rules = [
            CheckIpRule(),
            Cookies1RoutingRule(),
            Cookies2RoutingRule(),
            Cookies3RoutingRule(search_type=SHIPMENT_TYPE_MBL),
            MainRoutingRule(self._item_recorder, search_type=SHIPMENT_TYPE_MBL),
            ContainerRoutingRule(self._item_recorder),
            AvailabilityRoutingRule(self._item_recorder),
        ]

        booking_rules = [
            CheckIpRule(),
            Cookies1RoutingRule(),
            Cookies2RoutingRule(),
            Cookies3RoutingRule(search_type=SHIPMENT_TYPE_BOOKING),
            MainRoutingRule(self._item_recorder, search_type=SHIPMENT_TYPE_BOOKING),
            ContainerRoutingRule(self._item_recorder),
            AvailabilityRoutingRule(self._item_recorder),
        ]

        self._request_queue = RequestQueue()
        self._proxy_manager = ProxyManager(session='hdmu', logger=self.logger)

        if self.mbl_no:
            self._rule_manager = RuleManager(rules=bill_rules)
            self.search_no = self.mbl_no
        else:
            self._rule_manager = RuleManager(rules=booking_rules)
            self.search_no = self.booking_no

    def start(self):
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

                # # test
                # request = self._build_request_by(option=result)
                # self._request_queue.add(request=request)
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

        option = CheckIpRule.build_request_option(search_no=self.search_no)
        restart_proxy_option = self._proxy_manager.apply_proxy_to_request_option(option=option)
        restart_proxy_cookie_option = self._add_cookiejar_id_into_request_option(option=restart_proxy_option)
        return self._build_request_by(option=restart_proxy_cookie_option)

        # # test
        # return self._build_request_by(option=option)

    def _reformat_search_no_by(self, prefix_exist: bool):
        if prefix_exist:
            if self.search_no.startswith('HMDU'):
                return self.search_no
            else:
                return f'HDMU{self.search_no}'
        else:
            if self.search_no.startswith('HMDU'):
                return self.search_no[4:]
            else:
                return self.search_no

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


class CheckIpRule(BaseRoutingRule):
    name = 'IP'

    def __init__(self):
        self._sent_ips = []

    @classmethod
    def build_request_option(cls, search_no):
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=f'https://api.myip.com/',
            meta={
                'search_no': search_no,
            },
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.html'

    def handle(self, response):
        search_no = response.meta['search_no']

        response_dict = json.loads(response.text)
        ip = response_dict['ip']

        if ip in self._sent_ips:
            print(f'[WARNING][{self.__class__.__name__}] ---- ip repeated: `{ip}`')
            yield ForceRestart()
        else:
            self._sent_ips.append(ip)
            print(f'[INFO][{self.__class__.__name__}] ---- using ip: `{ip}`')
            yield Cookies1RoutingRule.build_request_option(search_no=search_no)


class Cookies1RoutingRule(BaseRoutingRule):
    name = 'COOKIES1'

    @classmethod
    def build_request_option(cls, search_no):
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=f'{BASE_URL}/cms/company/engn/index.jsp',
            # url=f'{BASE_URL}/ebiz/track_trace/main_new.jsp?null',
            headers={
                'Host': 'www.hmm21.com',
                'Accept': (
                    'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;'
                    'q=0.8,application/signed-exchange;v=b3;q=0.9'
                ),
                'Accept-Encoding': 'gzip, deflate, br',
                'User-Agent': (
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_1_0) AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/87.0.4280.141 Safari/537.36'
                ),
                'Connection': 'keep-alive',
                'Referer': 'https://www.hmm21.com/',
            },
            meta={
                'search_no': search_no,
            },
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.html'

    def handle(self, response):
        search_no = response.meta['search_no']

        cookies = self._extract_cookies_dict_from(response=response)

        if cookies:
            yield Cookies2RoutingRule.build_request_option(
                search_no=search_no, cookies=cookies)
        else:
            yield ForceRestart()

    @staticmethod
    def _extract_cookies_dict_from(response):
        cookies = {}
        for cookie_byte in response.headers.getlist('Set-Cookie'):
            kv = cookie_byte.decode('utf-8').split(';')[0].split('=')
            cookies[kv[0]] = kv[1]

        # return 'ak_bmsc' in cookies
        return cookies


class Cookies2RoutingRule(BaseRoutingRule):
    name = 'COOKIES2'

    @classmethod
    def build_request_option(cls, search_no, cookies: Dict):
        # bill_form_body = (
        #     'blFields=3&cnFields=3&'
        #     f'numbers={search_no}&numbers=&numbers=&numbers=&numbers=&numbers=&numbers=&numbers=&numbers=&'
        #     'numbers=&numbers=&numbers=&numbers=&numbers=&numbers=&numbers=&numbers=&numbers=&'
        #     'numbers=&numbers=&numbers=&numbers=&numbers=&numbers='
        # )
        #
        # booking_form_body = (
        #     'blFields=3&cnFields=3&'
        #     'numbers=&numbers=&numbers=&numbers=&numbers=&numbers=&numbers=&numbers=&numbers=&'
        #     'numbers=&numbers=&numbers=&numbers=&numbers=&numbers=&numbers=&numbers=&numbers=&'
        #     f'numbers={search_no}&numbers=&numbers=&numbers=&numbers=&numbers='
        # )

        # if search_type == BILL_OF_LADING:
        #     form_body = bill_form_body
        # else:
        #     form_body = booking_form_body

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=(
                f'{BASE_URL}/cms/business/ebiz/trackTrace/trackTrace/index.jsp?type=1&number={search_no}&'
                f'is_quick=Y&quick_params='
            ),
            headers={
                'Host': 'www.hmm21.com',
                'Upgrade-Insecure-Requests': '1',
                'Accept': (
                    'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;'
                    'q=0.8,application/signed-exchange;v=b3;q=0.9'
                ),
                'Accept-Encoding': 'gzip, deflate, br',
                'User-Agent': (
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_1_0) AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/87.0.4280.141 Safari/537.36'
                ),
                'Connection': 'keep-alive',
                'Referer': 'http://www.hmm21.com/cms/company/engn/index.jsp',
                'Cookie': CookieHelper.get_cookie_str(cookies),
            },
            meta={
                'search_no': search_no,
                'cookies': cookies,
            },
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.html'

    def handle(self, response):
        search_no = response.meta['search_no']
        cookies = response.meta['cookies']

        cookies.update(CookieHelper.get_cookies(response=response))

        if cookies:
            yield Cookies3RoutingRule.build_request_option(search_no=search_no, cookies=cookies)
            # yield MainRoutingRule.build_request_option(
            #     search_no=search_no, search_type=self._search_type, cookies=cookies)
        else:
            yield ForceRestart()


class Cookies3RoutingRule(BaseRoutingRule):
    name = 'COOKIES3'

    def __init__(self, search_type):
        self._search_type = search_type

    @classmethod
    def build_request_option(cls, search_no, cookies: Dict):
        # form_data = {
        #     'blFields': '3',
        #     'cnFields': '3',
        #     'numbers': [
        #         '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '',
        #     ],
        # }

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=f'{BASE_URL}/ebiz/track_trace/main_new.jsp?type=1&number={search_no}&is_quick=Y&quick_params=',
            headers={
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'User-Agent': (
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_1_0) AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/87.0.4280.141 Safari/537.36'
                ),
                'Accept': (
                    'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;'
                    'q=0.8,application/signed-exchange;v=b3;q=0.9'
                ),
                'Referer': (
                    f'{BASE_URL}/cms/business/ebiz/trackTrace/trackTrace/index.jsp?type=1&number={search_no}&'
                    f'is_quick=Y&quick_params='
                ),
                'Accept-Language': 'en-US,en;q=0.9',
                'Cookie': CookieHelper.get_cookie_str(cookies),
            },
            # form_data=form_data,
            meta={
                'search_no': search_no,
                'cookies': cookies,
            },
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.html'

    def handle(self, response):
        search_no = response.meta['search_no']
        cookies = response.meta['cookies']

        cookies.update(CookieHelper.get_cookies(response=response))

        if cookies:
            yield MainRoutingRule.build_request_option(
                search_no=search_no, search_type=self._search_type, cookies=cookies)
        else:
            yield ForceRestart()


# -------------------------------------------------------------------------------


class SpecificThTextExistMatchRule(BaseMatchRule):
    def __init__(self, text):
        self._text = text

    def check(self, selector: Selector) -> bool:
        ths = selector.css('th::text').getall()
        return self._text in ths


class MainRoutingRule(BaseRoutingRule):
    name = 'MAIN'

    def __init__(self, item_recorder: ItemRecorder, search_type):
        self._item_recorder = item_recorder
        self._search_type = search_type

    @classmethod
    def build_request_option(cls, search_no, search_type, cookies, under_line: bool = False):
        url_plug_in = '/_' if under_line else ''

        form_data = {
            'number': '',
            'type': '1',
            'selectedContainerIndex': '',
            'is_quick': 'Y',
            'blFields': '3',
            'cnFields': '3',
        }

        numbers = [('numbers', '')] * 24

        if search_type == SHIPMENT_TYPE_MBL:
            form_data['number'] = search_no
            numbers[0] = ('numbers', search_no)
        elif search_type == SHIPMENT_TYPE_BOOKING:
            numbers[18] = ('numbers', search_no)

        body = urlencode(query=form_data) + '&' + urlencode(numbers)

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_POST_BODY,
            url=f'{BASE_URL}{url_plug_in}/ebiz/track_trace/trackCTP_nTmp.jsp',
            headers={
                'Connection': 'keep-alive',
                'Cache-Control': 'max-age=0',
                'Upgrade-Insecure-Requests': '1',
                'Content-Type': 'application/x-www-form-urlencoded',
                'User-Agent': (
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_1_0) AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/87.0.4280.141 Safari/537.36'
                ),
                'Referer': (
                    f'{BASE_URL}/ebiz/track_trace/main_new.jsp?type=1&number={search_no}&is_quick=Y&quick_params=',
                ),
                'Accept-Language': 'en-US,en;q=0.9',
                'Cookie': CookieHelper.get_cookie_str(cookies),
            },
            body=body,
            meta={
                'search_no': search_no,
                'cookies': cookies,
                'under_line': under_line,
            },
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.html'

    def handle(self, response):
        search_no = response.meta['search_no']
        cookies = response.meta['cookies']
        under_line = response.meta['under_line']

        cookies.update(CookieHelper.get_cookies(response=response))
        if self._is_search_no_invalid(response=response):
            if not under_line:
                # retry to send other request with underline url
                # ex: {BASE_URL}/_/ebiz/track_trace/trackCTP_nTmp.jsp
                yield MainRoutingRule.build_request_option(
                    search_no=search_no, search_type=self._search_type, cookies=cookies, under_line=True)
                return

            raise CarrierInvalidSearchNoError(search_type=self._search_type)

        if not self._item_recorder.is_item_recorded(key=(MBL, search_no)):
            try:
                tracking_results = self._extract_tracking_results(response=response)
                customs_status = self._extract_customs_status(response=response)
                cargo_delivery_info = self._extract_cargo_delivery_info(response=response)
                latest_update = self._extract_lastest_update(response=response)
            except IndexError:
                yield ForceRestart()
                return

            mbl_item = MblItem(
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

            if self._search_type == SHIPMENT_TYPE_MBL:
                mbl_item['mbl_no'] = search_no
            elif self._search_type == SHIPMENT_TYPE_BOOKING:
                mbl_item['booking_no'] = search_no

            self._item_recorder.record_item(key=(MBL, search_no), item=mbl_item)

        if not self._item_recorder.is_item_recorded(key=(VESSEL, search_no)):
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
            self._item_recorder.record_item(key=(VESSEL, search_no), item=vessel_item)

        # parse other containers if there are many containers
        container_contents = self._extract_container_contents(response=response)
        h_num = -1
        for container_content in container_contents:
            if all(
                [
                    self._item_recorder.is_item_recorded(key=(CONTAINER, container_content.container_no)),
                    self._item_recorder.is_item_recorded(key=(AVAILABILITY, container_content.container_no)),
                ]
            ):
                continue

            elif container_content.is_current:
                response.meta['container_index'] = container_content.index

                container_routing_rule = ContainerRoutingRule(self._item_recorder)
                for result in container_routing_rule.handle(response=response):
                    yield result

            else:
                h_num -= 1
                yield ContainerRoutingRule.build_request_option(
                    search_no=search_no,
                    search_type=self._search_type,
                    container_index=container_content.index,
                    h_num=h_num,
                    cookies=cookies,
                    under_line=under_line,
                )

        # avoid this function not yield anything
        yield MblItem()

    @staticmethod
    def _is_search_no_invalid(response):
        err_message = response.css('div#trackingForm p.text_type03::text').get()
        err_message_underline = response.text.strip()
        if (
                isinstance(err_message, str) and
                'number is invalid.  Please try it again with correct number.' in err_message or
                err_message_underline == 'This page is not valid anymore.'
        ):
            return True
        return False

    @staticmethod
    def _extract_tracking_results(response):
        tables = response.css('#trackingForm div.base_table01')
        rule = SpecificThTextExistMatchRule(text='Origin')
        table_selector = find_selector_from(selectors=tables, rule=rule)

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
            css_query='::text', startswith='Cargo Delivery Information'
        )
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
        tables = response.css('#trackingForm div.base_table01')
        rule = SpecificThTextExistMatchRule(text='Nation / Item')
        table_selector = find_selector_from(selectors=tables, rule=rule)
        if not table_selector:
            return {
                'us_ams': None,
                'canada_aci': None,
                'eu_ens': None,
                'china_cams': None,
                'japan_afr': None,
            }

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
        tables = response.css('#trackingForm div.base_table01')
        rule = SpecificThTextExistMatchRule(text='Vessel / Voyage')
        table_selector = find_selector_from(selectors=tables, rule=rule)

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
            container_contents.append(
                ContainerContent(
                    container_no=container_no,
                    index=index,
                    is_current=is_current,
                )
            )
        return container_contents

    @staticmethod
    def _get_container_table(response):
        tables = response.css('#trackingForm div.base_table01')
        rule = SpecificThTextExistMatchRule(text='Container No.')
        container_table = find_selector_from(selectors=tables, rule=rule)

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
    def build_request_option(cls, search_no, search_type, container_index, h_num, cookies: Dict, under_line: bool = False):
        url_plug_in = '/_' if under_line else ''

        form_data = {
            'selectedContainerIndex': f'{container_index}',
            'hNum': f'{h_num}',
            'tempBLOrBKG': search_no,
            'numbers': [''] * 24,
        }

        if search_type == SHIPMENT_TYPE_MBL:
            form_data['numbers'][0] = search_no
        else:
            form_data['numbers'][18] = search_no
        body = urlencode(query=form_data)

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_POST_BODY,
            url=f'{BASE_URL}{url_plug_in}/ebiz/track_trace/trackCTP_nTmp.jsp?US_IMPORT=Y&BNO_IMPORT={search_no}',
            headers={
                'Connection': 'keep-alive',
                'Cache-Control': 'max-age=0',
                'Upgrade-Insecure-Requests': '1',
                'Origin': f'{BASE_URL}',
                'Content-Type': 'application/x-www-form-urlencoded',
                'User-Agent': (
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_1_0) AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/87.0.4280.141 Safari/537.36'
                ),
                'Accept': (
                    'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;'
                    'q=0.8,application/signed-exchange;v=b3;q=0.9'
                ),
                'Referer': f'{BASE_URL}/ebiz/track_trace/trackCTP_nTmp.jsp',
                'Accept-Language': 'en-US,en;q=0.9',
                'Cookie': CookieHelper.get_cookie_str(cookies),
            },
            body=body,
            meta={
                'search_no': search_no,
                'container_index': container_index,
                'cookies': cookies,
                'under_line': under_line,
            },
        )

    def get_save_name(self, response) -> str:
        container_index = response.meta['container_index']
        return f'{self.name}_{container_index}.html'

    def handle(self, response):
        search_no = response.meta['search_no']
        container_index = response.meta['container_index']
        under_line = response.meta['under_line']

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
                yield AvailabilityRoutingRule.build_request_option(
                    search_no=search_no, container_no=container_no, under_line=under_line)
            else:
                self._item_recorder.record_item(key=(AVAILABILITY, container_no))

        # avoid this function not yield anything
        yield MblItem()

    @staticmethod
    def _extract_tracking_results(response):
        tables = response.css('#trackingForm div.base_table01')
        rule = SpecificThTextExistMatchRule(text='Origin')
        table_selector = find_selector_from(selectors=tables, rule=rule)

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
        tables = response.css('#trackingForm div.base_table01')
        rule = SpecificThTextExistMatchRule(text='Date')
        table_selector = find_selector_from(selectors=tables, rule=rule)

        table_locator = TopHeaderTableLocator()
        table_locator.parse(table=table_selector)
        table = TableExtractor(table_locator=table_locator)

        container_status_list = []
        for index in table_locator.iter_left_header():
            date = table.extract_cell('Date', index)
            time = table.extract_cell('Time', index)
            location = table.extract_cell('Location', index, extractor=IgnoreDashTdExtractor())
            mode = table.extract_cell('Mode', index, extractor=IgnoreDashTdExtractor())

            container_status_list.append(
                {
                    'date': f'{date} {time}',
                    'location': location,
                    'status': table.extract_cell('Status Description', index),
                    'mode': mode,
                }
            )

        return container_status_list

    @staticmethod
    def _extract_availability_exist(response):
        ava_exist = response.xpath('//a[text()="Container Availability"]').get()
        return bool(ava_exist)

    @staticmethod
    def _extract_empty_return_location(response):
        table_exist_match_rule = CssQueryTextStartswithMatchRule(
            css_query='::text', startswith='Empty Container Return Location'
        )
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
        tables = response.css('#trackingForm div.base_table01')
        rule = SpecificThTextExistMatchRule(text='Container No.')
        container_table = find_selector_from(selectors=tables, rule=rule)

        return container_table


# -------------------------------------------------------------------------------


class AvailabilityRoutingRule(BaseRoutingRule):
    name = 'AVAILABILITY'

    def __init__(self, item_recorder: ItemRecorder):
        self._item_recorder = item_recorder

    @classmethod
    def build_request_option(cls, search_no, container_no, under_line: bool = False):
        url_plug_in = '/_' if under_line else ''

        form_data = {
            'bno': search_no,
            'cntrNo': f'{container_no}',
        }
        body = urlencode(query=form_data)

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_POST_BODY,
            url=f'{BASE_URL}{url_plug_in}/ebiz/track_trace/WUTInfo.jsp',
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
                'under_line': under_line,
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
        if table.has_header('STATUS', 0):
            return table.extract_cell('STATUS', 0)
        return None


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


class TopHeaderTableLocator(BaseTable):
    """
    +---------+---------+-----+---------+ <thead>
    | Title 1 | Title 2 | ... | Title N |     <th>
    +---------+---------+-----+---------+ </thead>
    +---------+---------+-----+---------+ <tbody>
    | Data    |         |     |         | <tr><td>
    +---------+---------+-----+---------+
    | Data    |         |     |         | <tr><td>
    +---------+---------+-----+---------+
    | ...     |         |     |         | <tr><td>
    +---------+---------+-----+---------+
    | Data    |         |     |         | <tr><td>
    +---------+---------+-----+---------+ </tbody>
    """
    def parse(self, table: Selector):
        top_header_list = []

        for th in table.css('thead th'):
            raw_top_header = th.css('::text').get()
            top_header = raw_top_header.strip() if isinstance(raw_top_header, str) else ''
            top_header_list.append(top_header)
            self._td_map[top_header] = []

        data_tr_list = table.css('tbody tr')
        for index, tr in enumerate(data_tr_list):
            self._left_header_set.add(index)
            for top, td in zip(top_header_list, tr.css('td')):
                self._td_map[top].append(td)


class TopLeftHeaderTableLocator(BaseTable):
    def parse(self, table: Selector):
        top_header_map = {}  # top_index: top_header

        for index, th in enumerate(table.css('thead th')):
            if index == 0:
                continue  # ignore top-left header

            top_header = th.css('::text').get().strip()
            top_header_map[index] = top_header
            self._td_map[top_header] = {}

        for tr in table.css('tbody tr'):
            td_list = list(tr.css('td'))

            left_header = td_list[0].css('::text').get().strip()
            self._left_header_set.add(left_header)

            for top_index, td in enumerate(td_list[1:], start=1):
                top = top_header_map[top_index]
                self._td_map[top][left_header] = td


class LeftHeaderTableLocator(BaseTable):
    def parse(self, table: Selector):
        for tr in table.css('tr'):
            left_header = tr.css('th ::text').get().strip()
            self._left_header_set.add(left_header)

            for top_index, td in enumerate(tr.css('td')):
                td_dict = self._td_map.setdefault(top_index, {})
                td_dict[left_header] = td
