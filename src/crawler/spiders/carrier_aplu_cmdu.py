import abc
import dataclasses
from typing import Dict

import scrapy
from scrapy import Selector

from crawler.core_carrier.exceptions import CarrierInvalidMblNoError, CarrierResponseFormatError
from crawler.core_carrier.items import BaseCarrierItem, MblItem, LocationItem, ContainerItem, ContainerStatusItem
from crawler.core_carrier.base_spiders import BaseCarrierSpider
from crawler.extractors.table_cell_extractors import BaseTableCellExtractor
from crawler.extractors.table_extractors import BaseTableLocator, TableExtractor, HeaderMismatchError
from crawler.utils.decorators import merge_yields


@dataclasses.dataclass
class UrlSpec:
    container_no: str = None


class UrlBuilder:

    def __init__(self, url_format: str):
        self._format = url_format

    def build_url_from_spec(self, spec: UrlSpec) -> str:
        return self._format.format(url_spec=spec)


class SharedUrlFactory:

    def __init__(self, home_url: str, mbl_no):
        self.mbl_no = mbl_no
        self.base = f'{home_url}/ebusiness/tracking'

    def get_bill_url_builder(self):
        url_format = f'{self.base}/search?SearchBy=BL&Reference={self.mbl_no}&search=Search'
        return UrlBuilder(url_format=url_format)

    def get_container_url_builder(self):
        url_format = f'{self.base}/detail/{{url_spec.container_no}}?SearchCriteria=BL&SearchByReference={self.mbl_no}'
        return UrlBuilder(url_format=url_format)


# -----------------------------------------------------------------------------------------------------------


class SharedSpider(BaseCarrierSpider):
    home_url = ''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        url_factory = SharedUrlFactory(home_url=self.home_url, mbl_no=self.mbl_no)

        self.routing_manager = RoutingManager()
        self.routing_manager.add_routing_rules(
            RoutingRule(
                name=HANDLE_FIRST_TIER,
                handler=FirstTierHandler(),
                url_builder=url_factory.get_bill_url_builder(),
            ),
            RoutingRule(
                name=HANDLE_CONTAINER,
                handler=ContainerHandler(),
                url_builder=url_factory.get_container_url_builder(),
            ),
        )

    def start_requests(self):
        require_req = RequireRequest(rule_name=HANDLE_FIRST_TIER, url_spec=UrlSpec())
        yield self.routing_manager.build_request_by(rule_name=require_req.rule_name, url_spec=require_req.url_spec)

    @merge_yields
    def parse(self, response):
        handler = self.routing_manager.get_handler_by_response(response=response)
        for result in handler.handle(response=response):
            if isinstance(result, BaseCarrierItem):
                yield result
            elif isinstance(result, RequireRequest):
                yield self.routing_manager.build_request_by(rule_name=result.rule_name, url_spec=result.url_spec)
            else:
                raise RuntimeError()


class CarrierApluSpider(SharedSpider):
    name = 'carrier_aplu'
    home_url = 'http://www.apl.com'


class CarrierCmduSpider(SharedSpider):
    name = 'carrier_cmdu'
    home_url = 'http://www.cma-cgm.com'


# -----------------------------------------------------------------------------------------------------------


class BaseHandler:

    @abc.abstractmethod
    def handle(self, response):
        pass


@dataclasses.dataclass
class RoutingRule:
    name: str
    handler: BaseHandler
    url_builder: UrlBuilder


class RoutingManager:
    META_ROUTING_RULE = 'ROUTING_RULE'

    def __init__(self):
        self._rule_map = {}

    def add_routing_rules(self, *rules: RoutingRule):
        for r in rules:
            self._rule_map[r.name] = r

    def get_handler_by_response(self, response) -> BaseHandler:
        rule_name = response.meta[self.META_ROUTING_RULE]
        return self._rule_map[rule_name].handler

    def build_request_by(self, rule_name: str, url_spec: UrlSpec) -> scrapy.Request:
        rule = self._rule_map[rule_name]
        assert isinstance(rule, RoutingRule)

        url = rule.url_builder.build_url_from_spec(spec=url_spec)

        request = scrapy.Request(url=url)
        request.meta[self.META_ROUTING_RULE] = rule_name
        return request


# -----------------------------------------------------------------------------------------------------------


HANDLE_FIRST_TIER = 'HANDLE_FIRST_TIER'
HANDLE_CONTAINER = 'HANDLE_CONTAINER'


@dataclasses.dataclass
class RequireRequest:
    rule_name: str
    url_spec: UrlSpec


class FirstTierHandler(BaseHandler):
    def handle(self, response):
        mbl_status = _MblStatusExtractor.extract(response=response)

        if mbl_status == STATUS_ONE_CONTAINER:
            container_handler = ContainerHandler()
            for item in container_handler.handle(response=response):
                yield item

        elif mbl_status == STATUS_MULTI_CONTAINER:
            container_list = _ContainerListExtractor.extract(response=response)

            for container in container_list:
                url_spec = UrlSpec(container_no=container)
                yield RequireRequest(rule_name=HANDLE_CONTAINER, url_spec=url_spec)

        else:  # STATUS_MBL_NOT_EXIST
            raise CarrierInvalidMblNoError()


class ContainerHandler(BaseHandler):
    def handle(self, response):
        container_info = _Extractor.extract_page_title(response=response)
        main_info = _Extractor.extract_tracking_no_map(response=response)

        yield MblItem(
            por=LocationItem(name=main_info['por']),
            pol=LocationItem(name=main_info['pol']),
            pod=LocationItem(name=main_info['pod']),
            final_dest=LocationItem(name=main_info['dest']),
            eta=main_info['pod_eta'],
            ata=main_info['pod_ata'],
        )

        container_no = container_info['container_no']

        yield ContainerItem(
            container_key=container_no,
            container_no=container_no,
        )

        for container_status in _ContainerStatusTableExtractor.extract(response=response):
            yield ContainerStatusItem(
                container_key=container_no,
                container_no=container_no,
                local_date_time=container_status['local_date_time'],
                description=container_status['description'],
                location=LocationItem(name=container_status['location']),
                est_or_actual=container_status['est_or_actual'],
            )


# -----------------------------------------------------------------------------------------------------------


class _Extractor:
    @staticmethod
    def extract_page_title(response: Selector):
        page_title_selector = response.css('div.o-pagetitle')

        return {
            'container_no': page_title_selector.css('span.o-pagetitle--container span::text').get(),
            'container_quantity': page_title_selector.css('span.o-pagetitle--container abbr::text').get(),
        }

    @staticmethod
    def extract_tracking_no_map(response: Selector):
        map_selector = response.css('div.o-trackingnomap')

        pod_time = map_selector.css('dl.o-trackingnomap--info dd::text').get()
        status = map_selector.css('dl.o-trackingnomap--info dt::text').get()
        if status is None:
            pod_eta = None
            pod_ata = None
        elif status.strip() == 'ETA at POD':
            pod_eta = pod_time.strip()
            pod_ata = None
        elif status.strip() == 'Arrived at POD':
            pod_eta = None
            pod_ata = pod_time.strip()
        elif status.strip() == 'Remaining':
            pod_eta = None
            pod_ata = None
        else:
            raise CarrierResponseFormatError(reason=f'Unknown status {status!r}')

        return {
            'por': map_selector.css('li#prepol span.o-trackingnomap--place::text').get(),
            'pol': map_selector.css('li#pol span.o-trackingnomap--place::text').get(),
            'pod': map_selector.css('li#pod span.o-trackingnomap--place::text').get(),
            'dest': map_selector.css('li#postpod span.o-trackingnomap--place::text').get(),
            'pod_eta': pod_eta,
            'pod_ata': pod_ata,
        }


# -----------------------------------------------------------------------------------------------------------


STATUS_ONE_CONTAINER = 'STATUS_ONE_CONTAINER'
STATUS_MULTI_CONTAINER = 'STATUS_MULTI_CONTAINER'
STATUS_MBL_NOT_EXIST = 'STATUS_MBL_NOT_EXIST'


class _MblStatusExtractor:

    @staticmethod
    def extract(response: Selector):
        result_message = response.css('div#wrapper h2::text').get()

        if result_message is None:
            return STATUS_ONE_CONTAINER
        elif result_message.strip() == 'Results':
            return STATUS_MULTI_CONTAINER
        else:
            return STATUS_MBL_NOT_EXIST


# -----------------------------------------------------------------------------------------------------------


class _ContainerListExtractor:
    @staticmethod
    def extract(response: Selector):
        container_list = response.css('td[data-ctnr=id] a::text').getall()
        return container_list


# -----------------------------------------------------------------------------------------------------------


class _ContainerStatusTableExtractor:
    @staticmethod
    def extract(response) -> Dict:
        table_selector = response.css('div.o-datatable table')
        table_locator = ContainerStatusTableLocator()
        table_locator.parse(table=table_selector)
        table = TableExtractor(table_locator=table_locator)

        for index, selector in enumerate(response.css('table tbody tr')):
            is_actual = bool(table.extract_cell('Status', index, extractor=ActualIconTdExtractor()))
            yield {
                'local_date_time': table.extract_cell('Date', index),
                'description': table.extract_cell('Moves', index),
                'location': table.extract_cell('Location', index),
                'est_or_actual': 'A' if is_actual else 'E',
            }


class ContainerStatusTableLocator(BaseTableLocator):

    def __init__(self):
        self._td_map = {}  # top_header: {left_index: td, ...}

    def parse(self, table: Selector):
        top_header_map = {}  # top_index: top_header

        for index, th in enumerate(table.css('thead th')):
            top_header_selector = th.css('::text').get()
            top_header = top_header_selector.strip()

            if index == 1:
                assert top_header == ''
                top_header = 'Status'

            top_header_map[index] = top_header
            self._td_map[top_header] = {}

        for left_index, tr in enumerate(table.css('tbody tr')):
            for top_index, td in enumerate(tr.css('td')):
                top = top_header_map[top_index]
                self._td_map[top][left_index] = td

    def get_cell(self, top, left) -> Selector:
        try:
            return self._td_map[top][left]
        except KeyError as err:
            raise HeaderMismatchError(repr(err))

    def has_header(self, top=None, left=None) -> bool:
        return (top in self._td_map) and (left is None)


class ActualIconTdExtractor(BaseTableCellExtractor):
    def extract(self, cell: Selector):
        td_i = cell.css('i').get()
        return td_i
