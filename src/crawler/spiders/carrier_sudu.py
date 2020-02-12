import dataclasses
import re

import scrapy
from scrapy import Selector

from crawler.core_carrier.base_spiders import BaseCarrierSpider
from crawler.core_carrier.rules import RuleManager, RoutingRequest, BaseRoutingRule, RoutingRequestQueue
from crawler.core_carrier.items import (
    BaseCarrierItem, MblItem, LocationItem, VesselItem, ContainerItem, ContainerStatusItem, ExportErrorData, DebugItem)
from crawler.core_carrier.exceptions import CarrierResponseFormatError, CarrierInvalidMblNoError, BaseCarrierError
from crawler.extractors.selector_finder import CssQueryTextStartswithMatchRule, find_selector_from, BaseMatchRule
from crawler.extractors.table_cell_extractors import BaseTableCellExtractor
from crawler.extractors.table_extractors import (
    BaseTableLocator, HeaderMismatchError, TableExtractor, TopHeaderTableLocator, TopLeftHeaderTableLocator)
from crawler.utils.decorators import merge_yields


class CarrierSuduSpider(BaseCarrierSpider):
    name = 'carrier_sudu'

    def __init__(self, *args, **kwargs):
        super(CarrierSuduSpider, self).__init__(*args, **kwargs)

        rules = [
            PageInfoRoutingRule(),
            SearchRoutingRule(),
            VoyageRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)
        self._request_queue = RoutingRequestQueue()

    def start_requests(self):
        routing_request = PageInfoRoutingRule.build_routing_request(mbl_no=self.mbl_no)
        yield self._rule_manager.build_request_by(routing_request=routing_request)

    def parse(self, response):
        yield DebugItem(info={'meta': dict(response.meta)})

        routing_rule = self._rule_manager.get_rule_by_response(response=response)

        save_name = routing_rule.get_save_name(response=response)
        self._saver.save(to=save_name, text=response.text)

        for result in routing_rule.handle(response=response):
            if isinstance(result, BaseCarrierItem):
                yield result
            elif isinstance(result, RoutingRequest):
                self._request_queue.add_request(result)
            else:
                raise RuntimeError()

        if not self._request_queue.is_empty():
            routing_request = self._request_queue.get_next_request()
            yield self._rule_manager.build_request_by(routing_request=routing_request)


# -------------------------------------------------------------------------------


class PageInfoRoutingRule(BaseRoutingRule):
    name = 'PAGE_INFO'

    @classmethod
    def build_routing_request(cls, mbl_no: str) -> RoutingRequest:
        request = scrapy.Request(
            url=f'https://www.hamburgsud-line.com/linerportal/pages/hsdg/tnt.xhtml',
            meta={'mbl_no': mbl_no},
            dont_filter=True,
        )
        return RoutingRequest(request=request, rule_name=cls.name)

    def handle(self, response):
        mbl_no = response.meta['mbl_no']

        view_state = response.css('input[name="javax.faces.ViewState"] ::attr(value)').get()
        j_idt = response.css('form ::attr(id)').get().strip(':searchForm')
        yield SearchRoutingRule.build_routing_request(
            BasicRequestSpec(mbl_no=mbl_no, view_state=view_state, j_idt=j_idt),
            is_first_process=True,
        )


# -------------------------------------------------------------------------------


CONTAINER_DETAIL = 'CONTAINER_DETAIL'
CONTAINER_LIST = 'CONTAINER_LIST'


@dataclasses.dataclass
class BasicRequestSpec:
    mbl_no: str
    view_state: str
    j_idt: str


class SearchRoutingRule(BaseRoutingRule):
    name = 'Search'

    def __init__(self):
        self._save_count = 0
        self._all_containers_set = set()
        self._processed_containers_set = set()
        self._container_form_info_map = {}  # container_no: form_info

    @classmethod
    def build_routing_request(
            cls,
            basic_request_spec: BasicRequestSpec,
            container_form_key=None,
            expect_view=None,
            is_first_process=False,
    ) -> RoutingRequest:

        j_idt2 = 'j_idt8' if basic_request_spec.j_idt == 'j_idt6' else 'j_idt9'
        search_form = f'{basic_request_spec.j_idt}:searchForm'
        form_data = {
            search_form: search_form,
            f'{search_form}:{j_idt2}:inputReferences': basic_request_spec.mbl_no,
            f'{search_form}:{j_idt2}:search-submit': f'{search_form}:{j_idt2}:search-submit',
            'javax.faces.ViewState': basic_request_spec.view_state,
        }
        if container_form_key:
            form_data[container_form_key] = container_form_key

        request = scrapy.FormRequest(
            url=f'https://www.hamburgsud-line.com/linerportal/pages/hsdg/tnt.xhtml',
            formdata=form_data,
            meta={
                'mbl_no': basic_request_spec.mbl_no,
                'expect_view': expect_view,
                'is_first_process': is_first_process,
            },
        )
        return RoutingRequest(request=request, rule_name=cls.name)

    def get_save_name(self, response):
        self._save_count += 1
        return f'{self.name}_{self._save_count}.html'

    @merge_yields
    def handle(self, response):
        mbl_no = response.meta['mbl_no']
        expect_view = response.meta['expect_view']
        is_first_process = response.meta['is_first_process']

        if is_first_process:
            self._check_mbl_no(response)

        # self.unprocessed_voyage_manager.check_empty()

        now_view = self._check_view(response=response, expect_view=expect_view)

        # request needed info
        view_state = response.css('input[name="javax.faces.ViewState"] ::attr(value)').get()
        j_idt = response.css('form ::attr(id)').get().strip(':searchForm')
        basic_request_spec = BasicRequestSpec(mbl_no=mbl_no, view_state=view_state, j_idt=j_idt)

        if now_view == CONTAINER_LIST:
            results = self._handle_list_page(
                response=response, basic_request_spec=basic_request_spec, is_first_process=is_first_process)
        elif now_view == CONTAINER_DETAIL:
            results = self._handle_detail_page(
                response=response, basic_request_spec=basic_request_spec, is_first_process=is_first_process)
        else:
            raise IncorrectValueError(value=now_view)

        for result in results:
            yield result

    @staticmethod
    def _check_mbl_no(response):
        error_message = response.css('span.ui-messages-info-summary::text').get()
        if error_message == 'No results found.':
            raise CarrierInvalidMblNoError()

    def _check_view(self, response, expect_view) -> str:
        if not expect_view:
            return self._determine_now_view(response)
        else:
            self._match_expect_view(response, expect_view)
            return expect_view

    @staticmethod
    def _match_expect_view(response, expect_view):

        if expect_view == CONTAINER_DETAIL:
            find_text = 'containerDetails_content'
        elif expect_view == CONTAINER_LIST:
            find_text = 'containerOverview_content'
        else:
            raise IncorrectValueError(value=expect_view)

        rule = CssQueryTextInMatchRule(css_query='::attr(id)', text=find_text)
        divs = response.css("div[class='ui-panel-content ui-widget-content']")

        if not find_selector_from(selectors=divs, rule=rule):
            raise CarrierResponseFormatError(reason=f'Page is not expected: `{expect_view}`')

    @staticmethod
    def _determine_now_view(response):
        # detail_div contains detail_table which is in detail page
        detail_div = response.css('div.ui-grid-responsive')

        if detail_div:
            return CONTAINER_DETAIL
        return CONTAINER_LIST

    def _handle_list_page(self, response, basic_request_spec: BasicRequestSpec, is_first_process: bool):
        if is_first_process:
            # prepare container data
            self._container_form_info_map = self._extract_container_form_info_map(response=response)
            for container_no, form_info in self._container_form_info_map.items():
                self._all_containers_set.add(container_no)

        if self._check_all_processed():
            return []

        container_form_info = self._get_next_container_form_info()

        return [
            SearchRoutingRule.build_routing_request(
                basic_request_spec=basic_request_spec,
                container_form_key=container_form_info,
                expect_view=CONTAINER_DETAIL,
            )
        ]

    def _handle_detail_page(self, response, basic_request_spec: BasicRequestSpec, is_first_process: bool):
        # parse
        main_info = self._extract_main_info(response=response)
        container_statuses = self._extract_container_statuses(response=response)
        container_no = main_info['container_no']
        por = main_info['por']
        final_dest = main_info['final_dest']

        if is_first_process:
            self._all_containers_set.add(container_no)

        if container_no in self._processed_containers_set:
            return []

        results = []

        mbl_item = MblItem(
            por=LocationItem(name=por),
            final_dest=LocationItem(name=final_dest),
            carrier_release_date=main_info['carrier_release_date'] or None,
            customs_release_date=main_info['customs_release_date'] or None,
        )
        results.append(mbl_item)

        container_item = ContainerItem(
            container_key=container_no,
            container_no=container_no,
        )
        results.append(container_item)

        for container_status in container_statuses:
            container_status = ContainerStatusItem(
                container_key=container_no,
                description=container_status['description'],
                local_date_time=container_status['timestamp'],
                location=LocationItem(name=container_status['location'] or None),
                vessel=container_status['vessel'] or None,
                voyage=container_status['voyage'] or None,
            )
            results.append(container_status)

        self._processed_containers_set.add(container_no)

        # voyage part
        departure_voyages = []
        arrival_voyages = []
        for container_status in container_statuses:
            vessel = container_status['vessel']
            location = container_status['location']

            if vessel and location == por:
                voyage_location = por
                voyage_direction = 'Departure'

                routing_request = VoyageRoutingRule.build_routing_request(
                    basic_request_spec=basic_request_spec,
                    voyage_key=container_status['voyage_css_id'],
                    voyage_location=voyage_location,
                    voyage_direction=voyage_direction,
                )
                departure_voyages.append(routing_request)

            elif vessel and location == final_dest:
                voyage_location = final_dest
                voyage_direction = 'Arrival'

                routing_request = VoyageRoutingRule.build_routing_request(
                    basic_request_spec=basic_request_spec,
                    voyage_key=container_status['voyage_css_id'],
                    voyage_location=voyage_location,
                    voyage_direction=voyage_direction,
                )
                arrival_voyages.append(routing_request)

        if departure_voyages:
            last_departure_voyage = departure_voyages[-1]
            results.append(last_departure_voyage)

        if arrival_voyages:
            if len(arrival_voyages) == 1:
                results.append(arrival_voyages[0])
            elif len(arrival_voyages) >= 2:
                raise CarrierResponseFormatError(reason='There are more than one `Departure from vessel`')

        if not self._check_all_processed():
            routing_request = SearchRoutingRule.build_routing_request(
                basic_request_spec=basic_request_spec, expect_view=CONTAINER_LIST)
            results.append(routing_request)

        return results

    def _check_all_processed(self):
        return self._all_containers_set == self._processed_containers_set

    def _get_next_container_form_info(self):
        not_processed_set = self._all_containers_set - self._processed_containers_set
        container_no = list(not_processed_set)[0]
        return self._container_form_info_map[container_no]

    @staticmethod
    def _extract_container_form_info_map(response):
        container_form_info = response.css('a[class="ui-commandlink ui-widget"]::attr(id)').getall()
        container_nos = response.css('a[class="ui-commandlink ui-widget"]::text').getall()

        container_form_info_map = {container_nos[i]: container_form_info[i] for i in range(len(container_nos))}
        return container_form_info_map

    @staticmethod
    def _extract_main_info(response):
        titles = response.css('h3')
        rule = CssQueryTextStartswithMatchRule(css_query='::text', startswith='Details')
        details_title = find_selector_from(selectors=titles, rule=rule)
        detail_div = details_title.xpath('./following-sibling::div')

        div_locator = MainDivTableLocator()
        div_locator.parse(table=detail_div)
        table = TableExtractor(table_locator=div_locator)

        if table.has_header(top='Carrier release'):
            carrier_release_date = table.extract_cell(top='Carrier release', left=None)
        else:
            carrier_release_date = ''

        if table.has_header(top='Customs release'):
            customs_release_date = table.extract_cell(top='Customs release', left=None)
        else:
            customs_release_date = ''

        return {
            'container_no': table.extract_cell(top='Container', left=None),
            'por': table.extract_cell(top='Origin', left=None),
            'final_dest': table.extract_cell(top='Destination', left=None),
            'carrier_release_date': carrier_release_date,
            'customs_release_date': customs_release_date,
        }

    @staticmethod
    def _extract_container_statuses(response):
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


class CssQueryTextInMatchRule(BaseMatchRule):
    def __init__(self, css_query: str, text: str):
        self._css_query = css_query
        self._text = text

    def check(self, selector: scrapy.Selector) -> bool:
        selected_text = selector.css(self._css_query).get()
        return self._text in selected_text

# -------------------------------------------------------------------------------


voyage_request_list = []


class VoyageRoutingRule(BaseRoutingRule):
    name = 'VOYAGE'

    @classmethod
    def build_routing_request(
            cls, basic_request_spec: BasicRequestSpec, voyage_key, voyage_location, voyage_direction) -> RoutingRequest:
        j_idt2 = 'j_idt8' if basic_request_spec.j_idt == 'j_idt6' else 'j_idt9'
        search_form = f'{basic_request_spec.j_idt}:searchForm'
        form_data = {
            search_form: search_form,
            f'{search_form}:{j_idt2}:inputReferences': basic_request_spec.mbl_no,
            'javax.faces.ViewState': basic_request_spec.view_state,
            voyage_key: voyage_key,
        }

        request = scrapy.FormRequest(
            url=f'https://www.hamburgsud-line.com/linerportal/pages/hsdg/tnt.xhtml',
            formdata=form_data,
            meta={
                'voyage_location': voyage_location,
                'voyage_direction': voyage_direction,
            }
        )

        return RoutingRequest(request=request, rule_name=cls.name)

    def get_save_name(self, response) -> str:
        voyage_location = response.meta['voyage_location']
        voyage_direction = response.meta['voyage_direction']

        return f'{self.name}_{voyage_location}_{voyage_direction}.html'

    @merge_yields
    def handle(self, response):
        voyage_location = response.meta['voyage_location']
        voyage_direction = response.meta['voyage_direction']

        voyage_routing = self._extract_voyage_routing(
            response=response, location=voyage_location, direction=voyage_direction)

        yield VesselItem(
            vessel_key=voyage_routing['vessel'],
            vessel=voyage_routing['vessel'],
            voyage=voyage_routing['voyage'],
            pol=LocationItem(name=voyage_routing['pol']),
            pod=LocationItem(name=voyage_routing['pod']),
            etd=voyage_routing['etd'],
            eta=voyage_routing['eta'],
        )

    def _extract_voyage_routing(self, response, location, direction):
        raw_vessel_voyage = response.css('h3::text').get()
        vessel, voyage = self._parse_vessel_voyage(raw_vessel_voyage)

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
    def _parse_vessel_voyage(vessel_voyage):
        pattern = re.compile(r'^Voyage details -\s+(?P<vessel>[\w+ ]+\w+) -\s+(?P<voyage>\w+)\s+$')
        match = pattern.match(vessel_voyage)
        if not match:
            raise CarrierResponseFormatError(reason=f'Unknown vessel_voyage title: `{vessel_voyage}`')

        return match.group('vessel'), match.group('voyage')


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
                td = scrapy.Selector(text=f'<td>{data.strip()}</td>')

                self._td_map[title.strip()] = td

    def get_cell(self, top, left) -> Selector:
        assert left is None
        try:
            return self._td_map[top]
        except KeyError as err:
            HeaderMismatchError(repr(err))

    def has_header(self, top=None, left=None) -> bool:
        return (top in self._td_map) and (left is None)


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
