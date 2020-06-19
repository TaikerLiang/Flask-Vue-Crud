from typing import Dict

import scrapy
from scrapy import Selector

from crawler.core_carrier.exceptions import CarrierInvalidMblNoError, CarrierResponseFormatError, \
    SuspiciousOperationError
from crawler.core_carrier.items import (
    BaseCarrierItem, MblItem, LocationItem, ContainerItem, ContainerStatusItem, DebugItem)
from crawler.core_carrier.base_spiders import BaseCarrierSpider
from crawler.core_carrier.request_helpers import RequestOption
from crawler.core_carrier.rules import RuleManager, BaseRoutingRule
from crawler.extractors.table_cell_extractors import BaseTableCellExtractor
from crawler.extractors.table_extractors import BaseTableLocator, TableExtractor, HeaderMismatchError


class SharedSpider(BaseCarrierSpider):
    name = None
    base_url = None

    def __init__(self, *args, **kwargs):
        super(SharedSpider, self).__init__(*args, **kwargs)

        rules = [
            FirstTierRoutingRule(base_url=self.base_url),
            ContainerStatusRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)

    def start(self):
        request_option = FirstTierRoutingRule.build_request_option(mbl_no=self.mbl_no, base_url=self.base_url)
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
                meta=meta,
            )
        else:
            raise SuspiciousOperationError(msg=f'Unexpected request method: `{option.method}`')


class CarrierApluSpider(SharedSpider):
    name = 'carrier_aplu'
    base_url = 'http://www.apl.com'


class CarrierCmduSpider(SharedSpider):
    name = 'carrier_cmdu'
    base_url = 'http://www.cma-cgm.com'


class CarrierAnlcSpider(SharedSpider):
    name = 'carrier_anlc'
    base_url = 'https://www.anl.com.au'


STATUS_ONE_CONTAINER = 'STATUS_ONE_CONTAINER'
STATUS_MULTI_CONTAINER = 'STATUS_MULTI_CONTAINER'
STATUS_MBL_NOT_EXIST = 'STATUS_MBL_NOT_EXIST'


class FirstTierRoutingRule(BaseRoutingRule):
    name = 'FIRST_TIER'

    def __init__(self, base_url):
        self.base_url = base_url

    @classmethod
    def build_request_option(cls, mbl_no, base_url) -> RequestOption:
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=f'{base_url}/ebusiness/tracking/search?SearchBy=BL&Reference={mbl_no}&search=Search',
            meta={'mbl_no': mbl_no},
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.html'

    def handle(self, response):
        mbl_no = response.meta['mbl_no']

        mbl_status = self._extract_mbl_status(response=response)

        if mbl_status == STATUS_ONE_CONTAINER:
            routing_rule = ContainerStatusRoutingRule()
            for item in routing_rule.handle(response=response):
                yield item

        elif mbl_status == STATUS_MULTI_CONTAINER:
            container_list = self._extract_container_list(response=response)

            for container_no in container_list:
                yield ContainerStatusRoutingRule.build_request_option(
                    mbl_no=mbl_no, container_no=container_no, base_url=self.base_url)

        else:  # STATUS_MBL_NOT_EXIST
            raise CarrierInvalidMblNoError()

    def _handle_container_status(self, response):
        pass

    @staticmethod
    def _extract_mbl_status(response: Selector):
        result_message = response.css('div#wrapper h2::text').get()

        if result_message is None:
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
    def build_request_option(cls, mbl_no, container_no, base_url) -> RequestOption:
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=f'{base_url}/ebusiness/tracking/detail/{container_no}?SearchCriteria=BL&SearchByReference={mbl_no}',
            meta={'container_no': container_no},
        )

    def get_save_name(self, response) -> str:
        container_no = response.meta['container_no']
        return f'container_status_{container_no}.html'

    def handle(self, response):
        container_info = self._extract_page_title(response=response)
        main_info = self._extract_tracking_no_map(response=response)

        yield MblItem(
            por=LocationItem(name=main_info['por']),
            pol=LocationItem(name=main_info['pol']),
            pod=LocationItem(name=main_info['pod']),
            final_dest=LocationItem(name=main_info['dest']),
            eta=main_info['pod_eta'],
        )

        container_no = container_info['container_no']

        yield ContainerItem(
            container_key=container_no,
            container_no=container_no,
        )

        container_status_list = self._extract_container_status(response=response)
        for container_status in container_status_list:
            yield ContainerStatusItem(
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
                'location': table.extract_cell('Location', index),
                'est_or_actual': 'A' if is_actual else 'E',
            }


# -----------------------------------------------------------------------------------------------------------


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
