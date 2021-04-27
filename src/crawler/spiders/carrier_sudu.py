import dataclasses
import re
from enum import Enum
from queue import Queue
from typing import Union, Tuple

from scrapy import Selector, FormRequest, Request

from crawler.core_carrier.base_spiders import BaseCarrierSpider
from crawler.core_carrier.request_helpers import RequestOption
from crawler.core_carrier.rules import RuleManager, BaseRoutingRule
from crawler.core_carrier.items import (
    BaseCarrierItem, MblItem, LocationItem, VesselItem, ContainerItem, ContainerStatusItem, ExportErrorData, DebugItem)
from crawler.core_carrier.exceptions import CarrierResponseFormatError, CarrierInvalidMblNoError, BaseCarrierError, \
    SuspiciousOperationError
from crawler.extractors.selector_finder import CssQueryTextStartswithMatchRule, find_selector_from, BaseMatchRule
from crawler.extractors.table_cell_extractors import BaseTableCellExtractor
from crawler.extractors.table_extractors import (
    BaseTableLocator, HeaderMismatchError, TableExtractor, TopHeaderTableLocator, TopLeftHeaderTableLocator)

BASE_URL = 'https://www.hamburgsud-line.com/linerportal/pages/hsdg/tnt.xhtml'


class MblState(Enum):
    FIRST = 'FIRST'
    SINGLE = 'SINGLE'
    MULTIPLE = 'MULTIPLE'


@dataclasses.dataclass
class BasicRequestSpec:
    mbl_no: str
    view_state: str
    j_idt: str


@dataclasses.dataclass
class VoyageSpec:
    direction: str
    container_key: str
    voyage_key: str
    location: str  # for debug purpose
    container_no: str  # for debug purpose


class RequestOptionFactory:

    @staticmethod
    def __build_form_data(basic_request_spec: BasicRequestSpec, container_link_element: str = ''):
        j_idt2 = 'j_idt8' if basic_request_spec.j_idt == 'j_idt6' else 'j_idt9'
        search_form = f'{basic_request_spec.j_idt}:searchForm'
        form_data = {
            search_form: search_form,
            f'{search_form}:{j_idt2}:inputReferences': basic_request_spec.mbl_no,
            f'{search_form}:{j_idt2}:search-submit': f'{search_form}:{j_idt2}:search-submit',
            'javax.faces.ViewState': basic_request_spec.view_state,
        }

        if container_link_element:
            form_data[container_link_element] = container_link_element

        return form_data

    @classmethod
    def build_search_option(cls, rule_name: str, basic_request_spec: BasicRequestSpec):
        form_data = cls.__build_form_data(basic_request_spec=basic_request_spec)

        return RequestOption(
            rule_name=rule_name,
            method=RequestOption.METHOD_POST_FORM,
            url=BASE_URL,
            form_data=form_data,
            meta={
                'mbl_no': basic_request_spec.mbl_no,
            },
        )

    @classmethod
    def build_container_option(
            cls, rule_name: str, basic_request_spec: BasicRequestSpec, container_link_element: str
    ) -> RequestOption:
        form_data = cls.__build_form_data(
            basic_request_spec=basic_request_spec, container_link_element=container_link_element
        )

        return RequestOption(
            rule_name=rule_name,
            url=BASE_URL,
            method=RequestOption.METHOD_POST_FORM,
            form_data=form_data,
            meta={
                'mbl_no': basic_request_spec.mbl_no,
            },
        )


class CarrierSuduSpider(BaseCarrierSpider):
    name = 'carrier_sudu'

    def __init__(self, *args, **kwargs):
        super(CarrierSuduSpider, self).__init__(*args, **kwargs)
        self._voyage_queue = Queue()
        self._voyage_queue_pusher = VoyageQueuePusher(queue=self._voyage_queue)
        self._voyage_queue_popper = VoyageQueuePopper(queue=self._voyage_queue)

        rules = [
            PageInfoRoutingRule(),
            MblSearchResultRoutingRule(voyage_queue_popper=self._voyage_queue_popper),
            ContainerDetailRoutingRule(voyage_queue_pusher=self._voyage_queue_pusher),
            VoyageRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)
        self._request_queue = RequestOptionQueue()

    def start(self):
        option = PageInfoRoutingRule.build_request_option(mbl_no=self.mbl_no)
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
                self._request_queue.add_request_option(result)
            else:
                raise RuntimeError()

        if not self._request_queue.is_empty():
            option = self._request_queue.get_next_request_option()
            yield self._build_request_by(option=option)

    def _build_request_by(self, option: RequestOption):
        meta = {
            RuleManager.META_CARRIER_CORE_RULE_NAME: option.rule_name,
            **option.meta,
        }

        if option.method == RequestOption.METHOD_GET:
            return Request(
                url=option.url,
                meta=meta,
                dont_filter=True,
            )
        elif option.method == RequestOption.METHOD_POST_FORM:
            return FormRequest(
                url=option.url,
                formdata=option.form_data,
                meta=meta,
            )
        else:
            raise SuspiciousOperationError(msg=f'Unexpected request method: `{option.method}`')


class VoyageQueuePopper:
    def __init__(self, queue: Queue):
        self._queue = queue

    def is_empty(self) -> bool:
        return self._queue.empty()

    def pop(self):
        return self._queue.get()


class VoyageQueuePusher:
    def __init__(self, queue: Queue):
        self._queue = queue

    def push(self, voyage: VoyageSpec):
        self._queue.put(voyage)


class RequestOptionQueue:

    def __init__(self):
        self._queue = []

    def is_empty(self):
        return not self._queue

    def add_request_option(self, option: RequestOption):
        self._queue.append(option)

    def get_next_request_option(self) -> Union[RequestOption, None]:
        return self._queue.pop(0)


# -------------------------------------------------------------------------------


class PageInfoRoutingRule(BaseRoutingRule):
    name = 'PAGE_INFO'

    @classmethod
    def build_request_option(cls, mbl_no: str) -> RequestOption:
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=BASE_URL,
            meta={'mbl_no': mbl_no},
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.html'

    def handle(self, response):
        mbl_no = response.meta['mbl_no']

        basic_request_spec = prepare_request_spec(mbl_no=mbl_no, response=response)

        yield MblSearchResultRoutingRule.build_request_option(
            basic_request_spec=basic_request_spec,
            mbl_state=MblState.FIRST,
        )


# -------------------------------------------------------------------------------


class MblSearchResultRoutingRule(BaseRoutingRule):
    name = 'MBL_SEARCH_RESULT'

    def __init__(self, voyage_queue_popper: VoyageQueuePopper):
        self._voyage_queue_popper = voyage_queue_popper
        self._save_count = 0
        self._containers_set = set()
        self._container_link_element_map = {}

    @classmethod
    def build_request_option(cls, basic_request_spec: BasicRequestSpec, mbl_state: MblState) -> RequestOption:
        search_option = RequestOptionFactory.build_search_option(
            rule_name=cls.name, basic_request_spec=basic_request_spec
        )
        option = search_option.copy_and_extend_by(meta={'mbl_state': mbl_state})

        return option

    def get_save_name(self, response):
        self._save_count += 1
        return f'{self.name}_{self._save_count}.html'

    def handle(self, response):
        """
        if there are multiple containers in mbl search result, you will get a container list page,
        then we need to save all container's number, mark mbl_state is MULTIPLE, and resend the request
        to MBLSearchResultRoutingRule.
        if there is a single container in mbl search result, you will get a container detail page,
        then we mark mbl_state is SINGLE and handle this page(Send to ContainerDetailRoutingRule).
        """
        mbl_no = response.meta['mbl_no']
        mbl_state = response.meta['mbl_state']

        if mbl_state == MblState.FIRST and self.__is_mbl_no_invalid(response):
            raise CarrierInvalidMblNoError()

        basic_request_spec = prepare_request_spec(mbl_no=mbl_no, response=response)

        if mbl_state == MblState.FIRST:
            if self.is_multi_containers(response=response):
                # prepare container data
                self._container_link_element_map = self.__extract_container_link_element_map(response=response)
                for container_no, form_info in self._container_link_element_map.items():
                    self._containers_set.add(container_no)

                # Because there is a dynamic token generated by JS for each request,
                # we don't iterate container id to send requests here.
                yield MblSearchResultRoutingRule.build_request_option(
                    basic_request_spec=basic_request_spec, mbl_state=MblState.MULTIPLE
                )
            else:
                yield ContainerDetailRoutingRule.build_request_option(
                    basic_request_spec=basic_request_spec, mbl_state=MblState.SINGLE
                )
        elif mbl_state == MblState.SINGLE:
            # Now, we know MblState is SINGLE, next we need to process voyage information.
            if self._voyage_queue_popper.is_empty():
                return []

            voyage_spec = self._voyage_queue_popper.pop()
            yield VoyageRoutingRule.build_request_option(
                basic_request_spec=basic_request_spec,
                voyage_spec=voyage_spec,
                mbl_state=mbl_state,
            )
        elif mbl_state == MblState.MULTIPLE:
            # Now, we know MblState is MULTIPLE means we know container number list.
            if self._voyage_queue_popper.is_empty():
                # If there is no voyage need to be processed then we use container number to
                # get container detail page and extract voyage information.
                if not self._containers_set:
                    return []
                container_no = self._containers_set.pop()
                container_link_element = self._container_link_element_map[container_no]
                yield ContainerDetailRoutingRule.build_request_option(
                    basic_request_spec=basic_request_spec,
                    container_link_element=container_link_element,
                    mbl_state=mbl_state,
                )
            else:
                # if there are some voyages in queue we need to process first, when the queue is empty, we will try to
                # handle next container detail page.
                voyage_spec = self._voyage_queue_popper.pop()
                yield ContainerDetailRoutingRule.build_request_option(
                    basic_request_spec=basic_request_spec,
                    mbl_state=mbl_state,
                    container_link_element=voyage_spec.container_key,
                    voyage_spec=voyage_spec,
                )
        else:
            raise SuspiciousOperationError(msg=f'Unexpected mbl_state: `{mbl_state}`')

    @staticmethod
    def __is_mbl_no_invalid(response):
        error_message = response.css('span.ui-messages-info-summary::text').get()
        if error_message == 'No results found.':
            return True

        return False

    @staticmethod
    def is_multi_containers(response):
        """
        Are there multiple containers in this mbl?
        """
        # detail_div contains detail_table which is in detail page
        detail_div = response.css('div.ui-grid-responsive')

        if detail_div:
            return False
        return True

    @staticmethod
    def __extract_container_link_element_map(response):
        container_link_elements = response.css('a[class="ui-commandlink ui-widget"]::attr(id)').getall()
        container_nos = response.css('a[class="ui-commandlink ui-widget"]::text').getall()

        container_link_element_map = {container_nos[i]: container_link_elements[i] for i in range(len(container_nos))}
        return container_link_element_map


# -------------------------------------------------------------------------------


class ContainerDetailRoutingRule(BaseRoutingRule):
    name = 'CONTAINER_DETAIL'

    def __init__(self, voyage_queue_pusher: VoyageQueuePusher):
        self._voyage_queue_pusher = voyage_queue_pusher

    @classmethod
    def build_request_option(
            cls,
            basic_request_spec: BasicRequestSpec,
            mbl_state: MblState,
            container_link_element: str = '',
            voyage_spec: VoyageSpec = None,
    ) -> RequestOption:
        if mbl_state == MblState.MULTIPLE:
            container_option = RequestOptionFactory.build_container_option(
                rule_name=cls.name, basic_request_spec=basic_request_spec, container_link_element=container_link_element
            )
        elif mbl_state == MblState.SINGLE:
            container_option = RequestOptionFactory.build_search_option(
                rule_name=cls.name, basic_request_spec=basic_request_spec
            )
        else:
            raise SuspiciousOperationError(msg=f'Unexpected mbl_state: `{mbl_state}`')

        option = container_option.copy_and_extend_by(meta={
                'container_key': container_link_element,  # for voyage purpose
                'voyage_spec': voyage_spec,
                'mbl_state': mbl_state,
        })

        return option

    def get_save_name(self, response) -> str:
        return f'{self.name}.html'

    def handle(self, response):
        """
        Voyage is empty, then
        - Extract container information include MblItem(), ContainerItem(), ContainerStatusItem()
        - Extract voyage information and put into queue

        Voyage is not empty, then
        - Click voyage link
        """
        mbl_no = response.meta['mbl_no']
        mbl_state = response.meta['mbl_state']
        voyage_spec = response.meta['voyage_spec']
        container_key = response.meta.get('container_key', '')

        basic_request_spec = prepare_request_spec(mbl_no=mbl_no, response=response)

        if not voyage_spec:
            for result in self.__handle_detail_page(response=response, container_key=container_key):
                if isinstance(result, BaseCarrierItem):
                    yield result
                elif isinstance(result, VoyageSpec):
                    self._voyage_queue_pusher.push(voyage=result)
                else:
                    raise RuntimeError()

            yield MblSearchResultRoutingRule.build_request_option(
                basic_request_spec=basic_request_spec, mbl_state=mbl_state
            )
        else:
            yield VoyageRoutingRule.build_request_option(
                basic_request_spec=basic_request_spec,
                voyage_spec=voyage_spec,
                mbl_state=mbl_state,
            )

    @classmethod
    def __handle_detail_page(cls, response, container_key: str):
        # parse
        main_info = cls.__extract_main_info(response=response)
        container_statuses = cls.__extract_container_statuses(response=response)
        container_no = main_info['container_no']
        por = main_info['por']
        final_dest = main_info['final_dest']

        yield MblItem(
            por=LocationItem(name=por),
            final_dest=LocationItem(name=final_dest),
            carrier_release_date=main_info['carrier_release_date'] or None,
            customs_release_date=main_info['customs_release_date'] or None,
        )

        yield ContainerItem(
            container_key=container_no,
            container_no=container_no,
        )

        for container_status in container_statuses:
            yield ContainerStatusItem(
                container_key=container_no,
                description=container_status['description'],
                local_date_time=container_status['timestamp'],
                location=LocationItem(name=container_status['location'] or None),
                vessel=container_status['vessel'] or None,
                voyage=container_status['voyage'] or None,
            )

        departure_voyage_spec, arrival_voyage_spec = cls.__get_container_voyage_link_element_specs(
            por=por,
            final_dest=final_dest,
            container_statuses=container_statuses,
            container_key=container_key,
            container_no=container_no,
        )

        if departure_voyage_spec:
            # push voyage_spec into Queue
            yield departure_voyage_spec

        if arrival_voyage_spec:
            # push voyage_spec into Queue
            yield arrival_voyage_spec

    @staticmethod
    def __extract_main_info(response):
        titles = response.css('h3')
        rule = CssQueryTextStartswithMatchRule(css_query='::text', startswith='Details')
        details_title = find_selector_from(selectors=titles, rule=rule)
        detail_div = details_title.xpath('./following-sibling::div')

        div_locator = MainDivTableLocator()
        div_locator.parse(table=detail_div)
        table = TableExtractor(table_locator=div_locator)

        carrier_release_date = ''
        if table.has_header(top='Carrier release'):
            carrier_release_date = table.extract_cell(top='Carrier release', left=None)

        customs_release_date = ''
        if table.has_header(top='Customs release'):
            customs_release_date = table.extract_cell(top='Customs release', left=None)

        return {
            'container_no': table.extract_cell(top='Container', left=None),
            'por': table.extract_cell(top='Origin', left=None),
            'final_dest': table.extract_cell(top='Destination', left=None),
            'carrier_release_date': carrier_release_date,
            'customs_release_date': customs_release_date,
        }

    @staticmethod
    def __extract_container_statuses(response):
        titles = response.css('h3')
        rule = CssQueryTextStartswithMatchRule(css_query='::text', startswith='Main information')
        main_info_title = find_selector_from(selectors=titles, rule=rule)
        main_info_div = main_info_title.xpath('./following-sibling::div')[0]

        table_selector = main_info_div.css('table')
        top_header_locator = TopHeaderTableLocator()
        top_header_locator.parse(table=table_selector)
        table = TableExtractor(table_locator=top_header_locator)
        vessel_voyage_extractor = VesselVoyageTdExtractor()

        container_statuses = []
        for left in top_header_locator.iter_left_header():
            vessel_voyage_info = table.extract_cell(top='Mode/Vendor', left=left, extractor=vessel_voyage_extractor)

            container_statuses.append({
                'timestamp': table.extract_cell(top='Date', left=left),
                'location': table.extract_cell(top='Place', left=left),
                'description': table.extract_cell(top='Movement', left=left),
                'vessel': vessel_voyage_info['vessel'],
                'voyage': vessel_voyage_info['voyage'],
                'voyage_css_id': vessel_voyage_info['voyage_css_id'],
            })

        container_statuses.reverse()

        return container_statuses

    @staticmethod
    def __get_container_voyage_link_element_specs(
            por, final_dest, container_statuses, container_key, container_no
    ) -> Tuple:
        # voyage part
        departure_voyages = []
        arrival_voyages = []
        for container_status in container_statuses:
            vessel = container_status['vessel']
            location = container_status['location']

            if vessel and location == por:
                voyage_spec = VoyageSpec(
                    direction='Departure',
                    container_key=container_key,
                    voyage_key=container_status['voyage_css_id'],
                    location=por,
                    container_no=container_no,
                )
                departure_voyages.append(voyage_spec)

            elif vessel and location == final_dest:
                voyage_spec = VoyageSpec(
                    direction='Arrival',
                    container_key=container_key,
                    voyage_key=container_status['voyage_css_id'],
                    location=final_dest,
                    container_no=container_no,
                )
                arrival_voyages.append(voyage_spec)

        first_departure_voyage = None
        if departure_voyages:
            first_departure_voyage = departure_voyages[0]

        last_arrival_voyage = None
        if arrival_voyages:
            last_arrival_voyage = arrival_voyages[-1]

        return first_departure_voyage, last_arrival_voyage


class VesselVoyageTdExtractor(BaseTableCellExtractor):

    def extract(self, cell: Selector):
        a_list = cell.css('a')

        if len(a_list) == 0:
            return {
                'vessel': '',
                'voyage': '',
                'voyage_css_id': '',
            }

        vessel_cell = a_list[0]
        voyage_cell = a_list[1]

        return {
            'vessel': vessel_cell.css('::text').get().strip(),
            'voyage': voyage_cell.css('::text').get().strip(),
            'voyage_css_id': voyage_cell.css('::attr(id)').get(),
        }


# -------------------------------------------------------------------------------


class VoyageRoutingRule(BaseRoutingRule):
    name = 'VOYAGE'

    @classmethod
    def build_request_option(
            cls, basic_request_spec: BasicRequestSpec, voyage_spec: VoyageSpec, mbl_state: MblState
    ) -> RequestOption:
        j_idt2 = 'j_idt8' if basic_request_spec.j_idt == 'j_idt6' else 'j_idt9'
        search_form = f'{basic_request_spec.j_idt}:searchForm'
        form_data = {
            search_form: search_form,
            f'{search_form}:{j_idt2}:inputReferences': basic_request_spec.mbl_no,
            'javax.faces.ViewState': basic_request_spec.view_state,
            voyage_spec.voyage_key: voyage_spec.voyage_key,
        }

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_POST_FORM,
            url=BASE_URL,
            form_data=form_data,
            meta={
                'mbl_state': mbl_state,
                'mbl_no': basic_request_spec.mbl_no,
                'voyage_location': voyage_spec.location,
                'voyage_direction': voyage_spec.direction,
            },
        )

    def get_save_name(self, response) -> str:
        voyage_location = response.meta['voyage_location']
        voyage_direction = response.meta['voyage_direction']

        return f'{self.name}_{voyage_location}_{voyage_direction}.html'

    def handle(self, response):
        mbl_no = response.meta['mbl_no']
        mbl_state = response.meta['mbl_state']
        voyage_location = response.meta['voyage_location']
        voyage_direction = response.meta['voyage_direction']

        if self._is_voyage_routing_connectable(response=response):
            voyage_routing = self.__extract_voyage_routing(
                response=response, location=voyage_location, direction=voyage_direction)

            yield VesselItem(
                vessel_key=f'{voyage_location} {voyage_direction}',
                vessel=voyage_routing['vessel'],
                voyage=voyage_routing['voyage'],
                pol=LocationItem(name=voyage_routing['pol']),
                pod=LocationItem(name=voyage_routing['pod']),
                etd=voyage_routing['etd'],
                eta=voyage_routing['eta'],
            )

        basic_request_spec = prepare_request_spec(mbl_no=mbl_no, response=response)

        yield MblSearchResultRoutingRule.build_request_option(
            basic_request_spec=basic_request_spec, mbl_state=mbl_state
        )

    @staticmethod
    def _is_voyage_routing_connectable(response: Selector) -> bool:
        return bool(response.css('h3'))

    def __extract_voyage_routing(self, response, location, direction):
        raw_vessel_voyage = response.css('h3::text').get()
        vessel, voyage = self.__parse_vessel_voyage(raw_vessel_voyage)

        table_selector = response.css('table[role="grid"]')
        if not table_selector:
            raise CarrierResponseFormatError(reason='Can not find voyage routing table !!!')

        top_left_locator = TopLeftHeaderTableLocator()
        top_left_locator.parse(table=table_selector)
        table = TableExtractor(table_locator=top_left_locator)

        eta, etd, pol, pod = None, None, None, None
        if direction == 'Arrival':
            eta = table.extract_cell(top='Estimated Arrival', left=location)
            pod = location

        elif direction == 'Departure':
            etd = table.extract_cell(top='Estimated Departure', left=location)
            pol = location

        else:
            raise CarrierResponseFormatError(reason=f'Unknown arr_or_dep: `{direction}`')

        return {
            'vessel': vessel,
            'voyage': voyage,
            'eta': eta,
            'etd': etd,
            'pol': pol,
            'pod': pod,
        }

    @staticmethod
    def __parse_vessel_voyage(vessel_voyage):
        pattern = re.compile(r'^Voyage details -\s+(?P<vessel>[\w+ ]+\w+) -\s+(?P<voyage>\w+)\s+$')
        match = pattern.match(vessel_voyage)
        if not match:
            raise CarrierResponseFormatError(reason=f'Unknown vessel_voyage title: `{vessel_voyage}`')

        return match.group('vessel'), match.group('voyage')


class TextExistsMatchRule(BaseMatchRule):
    def __init__(self, text: str):
        self._text = text

    def check(self, selector: Selector) -> bool:
        all_texts = selector.css('::text').getall()
        together_text = ''.join(all_texts)
        if self._text in together_text:
            return True
        return False


# -------------------------------------------------------------------------------


class IncorrectValueError(BaseCarrierError):

    def __init__(self, value):
        self.value = value

    def build_error_data(self):
        return ExportErrorData(status=self.status, detail=f'<incorrect-value-error> `{self.value}`')


class MainDivTableLocator(BaseTableLocator):

    def __init__(self):
        self._td_map = {}  # title: data

    def parse(self, table: Selector):
        div_section_list = table.css('div.ui-g')

        for div_section in div_section_list:

            cell_list = div_section.xpath('./div')
            for cell in cell_list:
                title, data = cell.css('::text').getall()
                td = Selector(text=f'<td>{data.strip()}</td>')

                self._td_map[title.strip()] = td

    def get_cell(self, top, left) -> Selector:
        assert left is None
        try:
            return self._td_map[top]
        except KeyError as err:
            HeaderMismatchError(repr(err))

    def has_header(self, top=None, left=None) -> bool:
        return (top in self._td_map) and (left is None)


class MBLSearchDispatcher:
    @staticmethod
    def is_multi_containers(response):
        """
        Are there multiple containers in this mbl?
        """
        # detail_div contains detail_table which is in detail page
        detail_div = response.css('div.ui-grid-responsive')

        if detail_div:
            return False
        return True


def prepare_request_spec(mbl_no: str, response) -> BasicRequestSpec:
    view_state = response.css('input[name="javax.faces.ViewState"] ::attr(value)').get()
    j_idt = response.css('form ::attr(id)').get().strip(':searchForm')

    return BasicRequestSpec(mbl_no=mbl_no, view_state=view_state, j_idt=j_idt)

