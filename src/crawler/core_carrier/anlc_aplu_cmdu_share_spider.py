import json
from typing import Dict

import scrapy
from scrapy import Selector

from crawler.core_carrier.base import SHIPMENT_TYPE_MBL, SHIPMENT_TYPE_BOOKING
from crawler.core_carrier.exceptions import (
    CarrierInvalidMblNoError, CarrierResponseFormatError, SuspiciousOperationError, DataNotFoundError,
    CarrierInvalidSearchNoError)

from crawler.core_carrier.items import (
    BaseCarrierItem,
    MblItem,
    LocationItem,
    ContainerItem,
    ContainerStatusItem,
    DebugItem,
    ExportData,
)
from crawler.core_carrier.base_spiders import BaseMultiCarrierSpider
from crawler.core_carrier.request_helpers import RequestOption, ProxyManager
from crawler.core_carrier.rules import RuleManager, BaseRoutingRule
from crawler.extractors.table_cell_extractors import BaseTableCellExtractor
from crawler.extractors.table_extractors import BaseTableLocator, TableExtractor, HeaderMismatchError

STATUS_ONE_CONTAINER = 'STATUS_ONE_CONTAINER'
STATUS_MULTI_CONTAINER = 'STATUS_MULTI_CONTAINER'
STATUS_MBL_NOT_EXIST = 'STATUS_MBL_NOT_EXIST'
STATUS_WEBSITE_SUSPEND = 'STATUS_WEBSITE_SUSPEND'


class ForceRestart:
    pass


class AnlcApluCmduShareSpider(BaseMultiCarrierSpider):
    name = ''
    base_url = ''

    def __init__(self, *args, **kwargs):
        super(AnlcApluCmduShareSpider, self).__init__(*args, **kwargs)

        bill_rules = [
            CheckIpRule(search_type=SHIPMENT_TYPE_MBL),
            FirstTierRoutingRule(search_type=SHIPMENT_TYPE_MBL),
            ContainerStatusRoutingRule(),
        ]

        booking_rules = [
            CheckIpRule(search_type=SHIPMENT_TYPE_BOOKING),
            FirstTierRoutingRule(search_type=SHIPMENT_TYPE_BOOKING),
            ContainerStatusRoutingRule(),
        ]

        if self.search_type == SHIPMENT_TYPE_MBL:
            self._rule_manager = RuleManager(rules=bill_rules)
        elif self.search_type == SHIPMENT_TYPE_BOOKING:
            self._rule_manager = RuleManager(rules=booking_rules)

        self._proxy_manager = ProxyManager(session='share', logger=self.logger)

    def start(self):
        for s_no, t_id in zip(self.search_nos, self.task_ids):
            option = self._prepare_start(search_no=s_no, task_id=t_id)
            yield self._build_request_by(option=option)

    def _prepare_start(self, search_no: str, task_id: str):
        self._proxy_manager.renew_proxy()
        option = CheckIpRule.build_request_option(search_no=search_no, base_url=self.base_url, task_id=task_id)
        proxy_option = self._proxy_manager.apply_proxy_to_request_option(option=option)
        return proxy_option

    def parse(self, response):
        yield DebugItem(info={'meta': dict(response.meta)})

        routing_rule = self._rule_manager.get_rule_by_response(response=response)
        save_name = routing_rule.get_save_name(response=response)
        self._saver.save(to=save_name, text=response.text)

        for result in routing_rule.handle(response=response):
            if isinstance(result, BaseCarrierItem):
                yield result
            elif isinstance(result, RequestOption):
                proxy_option = self._proxy_manager.apply_proxy_to_request_option(result)
                yield self._build_request_by(option=proxy_option)
            elif isinstance(result, ForceRestart):
                proxy_option = self._prepare_start()
                yield self._build_request_by(option=proxy_option)
            else:
                # raise RuntimeError()
                pass

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
            )
        elif option.method == RequestOption.METHOD_POST_FORM:
            return scrapy.FormRequest(
                url=option.url,
                headers=option.headers,
                formdata=option.form_data,
                meta=meta,
                dont_filter=True,
            )
        else:
            raise SuspiciousOperationError(msg=f'Unexpected request method: `{option.method}`')


class CheckIpRule(BaseRoutingRule):
    # TODO: Refactor later
    name = 'IP'

    def __init__(self, search_type):
        self._sent_ips = []
        self._search_type = search_type

    @classmethod
    def build_request_option(cls, base_url: str, search_no: str, task_id:str):
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=f'https://api.myip.com',
            meta={
                'search_no': search_no,
                'base_url': base_url,
                'task_id': task_id,
            },
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.html'

    def handle(self, response):
        search_no = response.meta['search_no']
        base_url = response.meta['base_url']
        task_id = response.meta['task_id']

        response_json = json.loads(response.text)
        ip = response_json['ip']

        if ip in self._sent_ips:
            yield ForceRestart()
            return

        self._sent_ips.append(ip)
        yield FirstTierRoutingRule.build_request_option(
            base_url=base_url, search_no=search_no, search_type=self._search_type, task_id=task_id)


class FirstTierRoutingRule(BaseRoutingRule):
    name = 'FIRST_TIER'

    def __init__(self, search_type):
        self._search_type = search_type

    @classmethod
    def build_request_option(cls, base_url: str, search_no: str, search_type: str, task_id: str) -> RequestOption:
        form_data = {
            'g-recaptcha-response': '',
            'SearchBy': 'BL' if search_type == SHIPMENT_TYPE_MBL else 'Booking',
            'Reference': search_no,
            'search': 'Search',
        }

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_POST_FORM,
            url=f'{base_url}/ebusiness/tracking/search',
            form_data=form_data,
            meta={
                'search_no': search_no,
                'base_url': base_url,
                'task_id': task_id,
            },
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.html'

    def handle(self, response):
        search_no = response.meta['search_no']
        base_url = response.meta['base_url']
        task_id = response.meta['task_id']

        mbl_status = self._extract_mbl_status(response=response)

        if self._search_type == SHIPMENT_TYPE_MBL:
            basic_mbl_item = MblItem(
                task_id=task_id,
                mbl_no=search_no
            )
        else:
            basic_mbl_item = MblItem(
                task_id=task_id,
                booking_no=search_no
            )

        if mbl_status == STATUS_ONE_CONTAINER:
            yield basic_mbl_item
            routing_rule = ContainerStatusRoutingRule()
            for item in routing_rule.handle(response=response):
                yield item

        elif mbl_status == STATUS_MULTI_CONTAINER:
            yield basic_mbl_item
            container_list = self._extract_container_list(response=response)

            for container_no in container_list:
                yield ContainerStatusRoutingRule.build_request_option(
                    container_no=container_no, base_url=base_url, search_no=search_no, search_type=self._search_type, task_id=task_id)

        elif mbl_status == STATUS_WEBSITE_SUSPEND:
            raise DataNotFoundError()

        else:  # STATUS_MBL_NOT_EXIST
            raise CarrierInvalidSearchNoError(search_type=self._search_type)

    @staticmethod
    def _extract_mbl_status(response: Selector):
        result_message = response.css('div#wrapper h2::text').get()

        maybe_suspend_message = response.css('h1 + p::text').get()

        if maybe_suspend_message == (
            'We have decided to temporarily suspend all access to our eCommerce websites to protect our customers.'
        ):
            return STATUS_WEBSITE_SUSPEND
        elif result_message is None:
            return STATUS_ONE_CONTAINER
        elif result_message.strip() == 'Results':
            return STATUS_MULTI_CONTAINER
        else:
            return STATUS_MBL_NOT_EXIST

    @staticmethod
    def _extract_container_list(response: Selector):
        container_list = response.css('td[data-ctnr=id] a::text').getall()
        return container_list


class ContainerStatusRoutingRule(BaseRoutingRule):
    name = 'CONTAINER_STATUS'

    @classmethod
    def build_request_option(cls, container_no: str, base_url: str, search_no: str, search_type: str, task_id: str) -> RequestOption:
        search_criteria = 'BL' if search_type == SHIPMENT_TYPE_MBL else 'Booking'
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=(
                f'{base_url}/ebusiness/tracking/detail/{container_no}?SearchCriteria={search_criteria}&'
                f'SearchByReference={search_no}'
            ),
            meta={
                'container_no': container_no,
                'task_id': task_id,
            },
        )

    def get_save_name(self, response) -> str:
        container_no = response.meta['container_no']
        return f'container_status_{container_no}.html'

    def handle(self, response):
        task_id = response.meta['task_id']

        container_info = self._extract_page_title(response=response)
        main_info = self._extract_tracking_no_map(response=response)

        yield MblItem(
            task_id=task_id,
            por=LocationItem(name=main_info['por']),
            pol=LocationItem(name=main_info['pol']),
            pod=LocationItem(name=main_info['pod']),
            final_dest=LocationItem(name=main_info['dest']),
            eta=main_info['pod_eta'],
        )

        container_no = container_info['container_no']

        yield ContainerItem(
            task_id=task_id,
            container_key=container_no,
            container_no=container_no,
        )

        container_status_list = self._extract_container_status(response=response)
        for container_status in container_status_list:
            yield ContainerStatusItem(
                task_id=task_id,
                container_key=container_no,
                local_date_time=container_status['local_date_time'],
                description=container_status['description'],
                location=LocationItem(name=container_status['location']),
                est_or_actual=container_status['est_or_actual'],
            )

    @staticmethod
    def _extract_page_title(response: Selector):
        page_title_selector = response.css('div.o-pagetitle')

        return {
            'container_no': page_title_selector.css('span.o-pagetitle--container span::text').get(),
            'container_quantity': page_title_selector.css('span.o-pagetitle--container abbr::text').get(),
        }

    @staticmethod
    def _extract_tracking_no_map(response: Selector):
        map_selector = response.css('div.o-trackingnomap')

        pod_time = map_selector.css('dl.o-trackingnomap--info dd::text').get()
        status = map_selector.css('dl.o-trackingnomap--info dt::text').get()
        if status is None:
            pod_eta = None
        elif status.strip() == 'ETA at POD':
            pod_eta = pod_time.strip()
        elif status.strip() == 'Arrived at POD':
            pod_eta = None
        elif status.strip() == 'Remaining':
            pod_eta = None
        else:
            raise CarrierResponseFormatError(reason=f'Unknown status {status!r}')

        return {
            'por': map_selector.css('li#prepol span.o-trackingnomap--place::text').get(),
            'pol': map_selector.css('li#pol span.o-trackingnomap--place::text').get(),
            'pod': map_selector.css('li#pod span.o-trackingnomap--place::text').get(),
            'dest': map_selector.css('li#postpod span.o-trackingnomap--place::text').get(),
            'pod_eta': pod_eta,
        }

    @staticmethod
    def _extract_container_status(response) -> Dict:
        table_selector = response.css('div.o-datatable table')
        table_locator = ContainerStatusTableLocator()
        table_locator.parse(table=table_selector)
        table = TableExtractor(table_locator=table_locator)

        for index in table_locator.iter_left_headers():
            is_actual = bool(table.extract_cell('Status', index, extractor=ActualIconTdExtractor()))
            yield {
                'local_date_time': table.extract_cell('Date', index),
                'description': table.extract_cell('Moves', index),
                'location': table.extract_cell('Location', index, LocationTdExtractor()),
                'est_or_actual': 'A' if is_actual else 'E',
            }


class ContainerStatusTableLocator(BaseTableLocator):
    def __init__(self):
        self._td_map = {}
        self._data_len = 0

    def parse(self, table: Selector):
        title_th_list = table.css('thead th')
        data_tr_list = table.css('tbody tr[class]')

        for title_index, title_th in enumerate(title_th_list):
            data_index = title_index

            title = title_th.css('::text').get().strip()

            if title_index == 1:
                assert title == ''
                title = 'Status'

            self._td_map[title] = []

            for data_tr in data_tr_list:
                data_td = data_tr.css('td')[data_index]

                self._td_map[title].append(data_td)

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


class ActualIconTdExtractor(BaseTableCellExtractor):
    def extract(self, cell: Selector):
        td_i = cell.css('i').get()
        return td_i


class LocationTdExtractor(BaseTableCellExtractor):
    def extract(self, cell: Selector):
        td_i = cell.css('td::text').get().strip()
        return td_i