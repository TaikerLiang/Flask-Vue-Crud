import re
from typing import Union, Tuple

import scrapy

from crawler.core_carrier.base_spiders import BaseCarrierSpider
from crawler.core_carrier.exceptions import CarrierResponseFormatError, CarrierInvalidMblNoError
from crawler.core_carrier.items import BaseCarrierItem, ContainerStatusItem, LocationItem, MblItem, ContainerItem
from crawler.core_carrier.rules import BaseRoutingRule, RoutingRequest, RuleManager
from crawler.extractors.table_cell_extractors import BaseTableCellExtractor, FirstTextTdExtractor
from crawler.extractors.table_extractors import BaseTableLocator, HeaderMismatchError, TableExtractor
from crawler.utils.decorators import merge_yields

BASE_URL = 'https://www.yangming.com/e-service/Track_Trace'


class CarrierYmluSpider(BaseCarrierSpider):
    name = 'carrier_ymlu'

    def __init__(self, *args, **kwargs):
        super(CarrierYmluSpider, self).__init__(*args, **kwargs)

        rules = [
            MainInfoRoutingRule(),
            ContainerStatusRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)

    def start_requests(self):
        routing_request = MainInfoRoutingRule.build_routing_request(mbl_no=self.mbl_no)
        yield self._rule_manager.build_request_by(routing_request=routing_request)

    @merge_yields
    def parse(self, response):
        routing_rule = self._rule_manager.get_rule_by_response(response=response)

        for result in routing_rule.handle(response=response):
            if isinstance(result, BaseCarrierItem):
                yield result
            elif isinstance(result, RoutingRequest):
                yield self._rule_manager.build_request_by(routing_request=result)
            else:
                raise RuntimeError()


class MainInfoRoutingRule(BaseRoutingRule):
    name = 'MAIN_INFO'

    @classmethod
    def build_routing_request(cls, mbl_no: str) -> RoutingRequest:
        url = f'{BASE_URL}/blconnect.aspx?BLADG={mbl_no},&rdolType=BL&type=cargo'
        request = scrapy.Request(url=url)
        return RoutingRequest(rule_name=cls.name, request=request)

    def handle(self, response):
        self._check_main_info(response=response)

        mbl_no = self._extract_mbl_no(response=response)
        basic_info = self._extract_basic_info(response=response)
        pol = basic_info['pol']
        pod = basic_info['pod']

        routing_schedule = self._extract_routing_schedule(response=response, pol=pol, pod=pod)
        firms_code = self._extract_firms_code(response=response)
        release_status = self._extract_release_status(response=response)

        yield MblItem(
            mbl_no=mbl_no,
            por=LocationItem(name=basic_info['por']),
            pol=LocationItem(name=pol),
            pod=LocationItem(name=pod),
            place_of_deliv=LocationItem(name=basic_info['place_of_deliv']),
            etd=routing_schedule['etd'],
            atd=routing_schedule['atd'],
            eta=routing_schedule['eta'],
            ata=routing_schedule['ata'],
            firms_code=firms_code,
            carrier_status=release_status['carrier_status'],
            carrier_release_date=release_status['carrier_release_date'],
            customs_release_status=release_status['customs_release_status'],
            customs_release_date=release_status['customs_release_date'],
        )

        last_free_day_dict = self._extract_last_free_day(response=response)
        container_info_list = self._extract_container_info(response=response)

        for container_info in container_info_list:
            container_no = container_info['container_no']
            last_free_day = last_free_day_dict.get(container_no)

            yield ContainerItem(
                container_key=container_no,
                container_no=container_no,
                last_free_day=last_free_day
            )

            follow_url = container_info['follow_url']
            yield ContainerStatusRoutingRule.build_routing_request(
                response=response, follow_url=follow_url, container_no=container_no)

    @staticmethod
    def _check_main_info(response):
        no_data_found_selector = response.css('div#ContentPlaceHolder1_rptBLNo_divNoDataFound_0')
        style = no_data_found_selector.css('::attr(style)').get()

        if 'display: none' in style:
            # Error message is hide
            return

        # Error message is shown
        raise CarrierInvalidMblNoError()

    @staticmethod
    def _extract_mbl_no(response: scrapy.Selector):
        mbl_no = response.css('span#ContentPlaceHolder1_rptBLNo_lblBLNo_0::text').get()
        return mbl_no.strip()

    @staticmethod
    def _extract_basic_info(response: scrapy.Selector):
        table_selector = response.css('table#ContentPlaceHolder1_rptBLNo_gvBasicInformation_0')

        table_locator = TopHeaderIsTdTableLocator()
        table_locator.parse(table=table_selector)
        table = TableExtractor(table_locator=table_locator)

        span_text_td_extractor = TdExtractorFactory.build_span_text_td_extractor()

        return {
            'por': table.extract_cell(top='Receipt', left=None, extractor=span_text_td_extractor) or None,
            'pol': table.extract_cell(top='Loading', left=None, extractor=span_text_td_extractor) or None,
            'pod': table.extract_cell(top='Discharge', left=None, extractor=span_text_td_extractor) or None,
            'place_of_deliv': table.extract_cell(
                top='Delivery', left=None, extractor=span_text_td_extractor) or None,
        }

    @staticmethod
    def _extract_routing_schedule(response: scrapy.Selector, pol: str, pod: str):
        table_selector = response.css('table#ContentPlaceHolder1_rptBLNo_gvRoutingSchedule_0')

        table_locator = TopHeaderIsTdTableLocator()
        table_locator.parse(table=table_selector)
        table = TableExtractor(table_locator=table_locator)

        span_text_td_extractor = TdExtractorFactory.build_span_text_td_extractor()

        etd, atd, eta, ata = None, None, None, None
        for left in table_locator.iter_left_headers():
            place = table.extract_cell(top='Routing', left=left, extractor=span_text_td_extractor)
            time_status = table.extract_cell(top='ETD/ETA', left=left, extractor=span_text_td_extractor)

            actual_time, estimated_time = MainInfoRoutingRule._parse_time_status(time_status)

            if pol.startswith(place):
                atd = actual_time
                etd = estimated_time
            elif pod.startswith(place):
                ata = actual_time
                eta = estimated_time

        return {
            'etd': etd,
            'atd': atd,
            'eta': eta,
            'ata': ata,
        }

    @staticmethod
    def _parse_time_status(time_status) -> Tuple[str, str]:
        """
        time_status = 'YYYY/MM/DD HH:mm (Actual/Estimated)'
        """
        patt = re.compile(r'^(?P<date_time>\d{4}/\d{2}/\d{2} \d{2}:\d{2}) [(](?P<status>Actual|Estimated)[)]$')

        m = patt.match(time_status)
        if not m:
            raise CarrierResponseFormatError(reason=f'Routing Schedule time format error: {time_status}')

        time, status = m.group('date_time'), m.group('status')
        actual_time = time if status == 'Actual' else None
        estimated_time = time if status == 'Estimated' else None

        return actual_time, estimated_time

    @staticmethod
    def _extract_container_info(response):
        table_selector = response.css('table#ContentPlaceHolder1_rptBLNo_gvLatestEvent_0')

        table_locator = TopHeaderIsTdTableLocator()
        table_locator.parse(table=table_selector)
        table = TableExtractor(table_locator=table_locator)

        a_text_td_extractor = TdExtractorFactory.build_a_text_td_extractor()
        a_href_td_extractor = TdExtractorFactory.build_a_href_extractor()

        container_info_list = []
        for left in table_locator.iter_left_headers():
            container_no = table.extract_cell(top='Container No.', left=left, extractor=a_text_td_extractor)
            follow_url = table.extract_cell(top='Container No.', left=left, extractor=a_href_td_extractor)

            container_info_list.append({
                'container_no': container_no,
                'follow_url': follow_url,
            })

        return container_info_list

    @staticmethod
    def _extract_release_status(response):
        """
        case 1: 'Customs Status : (No entry filed)' appear in page
            carrier_status_with_date = None
            custom_status = '(No entry filed)'
        case 2: Both customs status and carrier status are not in page
            carrier_status_with_date = 'Label'
            custom_status = 'Label'
        """
        carrier_status_with_date = response.css('span#ContentPlaceHolder1_rptBLNo_lblCarrierStatus_0::text').get()
        if carrier_status_with_date in [None, 'Label']:
            carrier_status, carrier_date = None, None
        else:
            carrier_status_with_date = carrier_status_with_date.strip()
            carrier_status, carrier_date = MainInfoRoutingRule._parse_carrier_status(carrier_status_with_date)

        customs_status = response.css('span#ContentPlaceHolder1_rptBLNo_lblCustomsStatus_0::text').get()
        if customs_status in ['(No entry filed)', 'Label']:
            customs_status = None
            customs_date = None
        else:
            customs_table_selector = response.css('table#ContentPlaceHolder1_rptBLNo_gvCustomsStatus_0')

            table_locator = TopHeaderIsTdTableLocator()
            table_locator.parse(table=customs_table_selector)
            table = TableExtractor(table_locator=table_locator)

            span_text_td_extractor = TdExtractorFactory.build_span_text_td_extractor()

            customs_date = None
            for left in table_locator.iter_left_headers():
                event_code = table.extract_cell(top='Event', left=left, extractor=span_text_td_extractor)
                if event_code == '1C':
                    customs_date = table.extract_cell(top='Date/Time', left=left, extractor=span_text_td_extractor)
                    break

        return {
            'carrier_status': carrier_status,
            'carrier_release_date': carrier_date,
            'customs_release_status': customs_status,
            'customs_release_date': customs_date,
        }

    @staticmethod
    def _parse_carrier_status(carrier_status_with_date) -> Tuple[str, str]:
        """
        carrier_status_with_date = 'carrier_status YYYY/MM/DD HH:mm'
        """
        patt = re.compile(r'(?P<status>.+)\s+(?P<release_date>\d{4}/\d{2}/\d{2} \d{2}:\d{2})')

        m = patt.match(carrier_status_with_date)
        if m is None:
            raise CarrierResponseFormatError(reason=f'Carrier Status format error: `{carrier_status_with_date}`')

        status = m.group('status').strip()
        release_date = m.group('release_date').strip()
        return status, release_date

    @staticmethod
    def _extract_firms_code(response: scrapy.Selector):
        # [0]WEST BASIN CONTAINER TERMINAL [1](Firms code:Y773)
        discharged_port_terminal_text = \
            response.css('span#ContentPlaceHolder1_rptBLNo_lblDischarged_0 ::text').getall()
        if len(discharged_port_terminal_text) == 1:
            return None
        elif len(discharged_port_terminal_text) > 2:
            error_message = f'Discharged Port Terminal format error: `{discharged_port_terminal_text}`'
            raise CarrierResponseFormatError(reason=error_message)

        firms_code_text = discharged_port_terminal_text[1]
        firms_code = MainInfoRoutingRule._parse_firms_code(firms_code_text)
        return firms_code

    @staticmethod
    def _parse_firms_code(firms_code_text):
        """
        firms_code_text = '(Firms code:Y123)'
        """
        pat = re.compile(r'.+:(?P<firms_code>\w{4})')

        m = pat.match(firms_code_text)
        if m is None:
            raise CarrierResponseFormatError(reason=f'Firms Code format error: `{firms_code_text}`')

        return m.group('firms_code')

    @staticmethod
    def _extract_last_free_day(response):
        table_selector = response.css('table#ContentPlaceHolder1_rptBLNo_gvLastFreeDate_0')
        if table_selector is None:
            return {}

        table_locator = TopHeaderThInTbodyTableLocator()
        table_locator.parse(table=table_selector)
        table = TableExtractor(table_locator=table_locator)

        span_text_td_extractor = TdExtractorFactory.build_span_text_td_extractor()

        last_free_day_dict = {}  # container_no: last_free_day
        for left in table_locator.iter_left_headers():
            container_no = table.extract_cell(top='Container No.', left=left, extractor=span_text_td_extractor)

            last_free_date = None
            for top in ['Ramp Last Free Date', 'Terminal Last Free Date']:
                if table.has_header(top=top):
                    last_free_date = table.extract_cell(top=top, left=left, extractor=span_text_td_extractor)

            last_free_day_dict[container_no] = last_free_date

        return last_free_day_dict


class TopHeaderThInTbodyTableLocator(BaseTableLocator):
    """
    +----------+----------+-----+----------+ <tbody>
    | Titie 1  | Title 2  | ... | Title N  | <tr> <th>
    +----------+----------+-----+----------+
    | Data 1,1 | Data 2,1 | ... | Data N,1 | <tr> <td>
    +----------+----------+-----+----------+
    | Data 1,2 | Data 2,2 | ... | Data N,2 | <tr> <td>
    +----------+----------+-----+----------+
    | ...      | ...      | ... | ...      |
    +----------+----------+-----+----------+
    | Data 1,M | Data 2,M | ... | Data N,M | <tr> <td>
    +----------+----------+-----+----------+ <\tbody>
    """
    TR_DATA_BEGIN = 1

    def __init__(self):
        self._td_map = {}  # top_header: [td, ...]
        self._data_len = 0

    def parse(self, table: scrapy.Selector):
        title_td_list = table.css('th')
        data_tr_list = table.css('tr')[self.TR_DATA_BEGIN:]

        for title_index, title_td in enumerate(title_td_list):
            data_index = title_index

            title = title_td.css('::text').get().strip()
            self._td_map[title] = []

            for data_tr in data_tr_list:
                data_td = data_tr.css('td')[data_index]

                self._td_map[title].append(data_td)

        self._data_len = len(data_tr_list)

    def get_cell(self, top, left: Union[int, None]) -> scrapy.Selector:
        try:
            left = 0 if left is None else left
            return self._td_map[top][left]
        except (KeyError, IndexError) as err:
            raise HeaderMismatchError(repr(err))

    def has_header(self, top=None, left=None) -> bool:
        return (top in self._td_map) and (left is None)

    def iter_left_headers(self):
        for index in range(self._data_len):
            yield index


# --------------------------------------------------------------------


class ContainerStatusRoutingRule(BaseRoutingRule):
    name = 'CONTAINER_STATUS'

    @classmethod
    def build_routing_request(cls, response, follow_url: str, container_no: str) -> RoutingRequest:
        request = response.follow(follow_url)
        request.meta['container_no'] = container_no
        return RoutingRequest(request=request, rule_name=cls.name)

    def handle(self, response):
        container_no = response.meta['container_no']

        container_status_list = self._extract_container_status(response=response)
        for container_status in container_status_list:
            yield ContainerStatusItem(
                container_key=container_no,
                description=container_status['description'],
                local_date_time=container_status['timestamp'],
                location=LocationItem(name=container_status['location_name']),
                transport=container_status['transport'] or None,
            )

    @staticmethod
    def _extract_container_status(response):
        table_selector = response.css('table#ContentPlaceHolder1_gvContainerNo')

        table_locator = TopHeaderIsTdTableLocator()
        table_locator.parse(table=table_selector)
        table = TableExtractor(table_locator=table_locator)

        span_text_td_extractor = TdExtractorFactory.build_span_text_td_extractor()
        span_all_text_td_extractor = SpanAllTextTdExtractor()

        container_stauts_list = []
        for left in table_locator.iter_left_headers():
            container_stauts_list.append({
                'timestamp': table.extract_cell(top='Date/Time', left=left, extractor=span_text_td_extractor),
                'description': table.extract_cell(top='Event', left=left, extractor=span_text_td_extractor),
                'location_name': table.extract_cell(
                    top='At Facility', left=left, extractor=span_all_text_td_extractor),
                'transport': table.extract_cell(top='Mode', left=left, extractor=span_all_text_td_extractor),
            })

        return container_stauts_list


# --------------------------------------------------------------------


class TopHeaderIsTdTableLocator(BaseTableLocator):
    """
    +----------+----------+-----+----------+ <thead>
    | Title 1  | Title 2  | ... | Title N  | <tr> <td>
    +----------+----------+-----+----------+ <\thead>
    +----------+----------+-----+----------+ <tbody>
    | Data 1,1 | Data 2,1 | ... | Data N,1 | <tr> <td>
    +----------+----------+-----+----------+
    | Data 1,2 | Data 2,2 | ... | Data N,2 | <tr> <td>
    +----------+----------+-----+----------+
    | ...      |   ...    | ... |   ...    | <tr> <td>
    +----------+----------+-----+----------+
    | Data 1,M | Data 2,M | ... | Data N,M | <tr> <td>
    +----------+----------+-----+----------+ <\tbody>
    """

    def __init__(self):
        self._td_map = {}  # top_header: [td, ...]
        self._data_len = 0

    def parse(self, table: scrapy.Selector):
        title_td_list = table.css('thead td')
        data_tr_list = table.css('tbody tr')

        for title_index, title_td in enumerate(title_td_list):
            data_index = title_index

            title = title_td.css('::text').get().strip()
            self._td_map[title] = []

            for data_tr in data_tr_list:
                data_td = data_tr.css('td')[data_index]

                self._td_map[title].append(data_td)

        self._data_len = len(data_tr_list)

    def get_cell(self, top, left: Union[int, None]) -> scrapy.Selector:
        try:
            left = 0 if left is None else left
            return self._td_map[top][left]
        except (KeyError, IndexError) as err:
            raise HeaderMismatchError(repr(err))

    def has_header(self, top=None, left=None) -> bool:
        return (top in self._td_map) and (left is None)

    def iter_left_headers(self):
        for index in range(self._data_len):
            yield index


# --------------------------------------------------------------------


class TdExtractorFactory:
    @staticmethod
    def build_span_text_td_extractor():
        return FirstTextTdExtractor('span::text')

    @staticmethod
    def build_a_text_td_extractor():
        return FirstTextTdExtractor('a::text')

    @staticmethod
    def build_a_href_extractor():
        return FirstTextTdExtractor('a::attr(href)')


class SpanAllTextTdExtractor(BaseTableCellExtractor):
    def __init__(self, css_query: str = 'span::text'):
        self.css_query = css_query

    def extract(self, cell: scrapy.Selector):
        all_text = cell.css(self.css_query).getall()
        text = ' '.join(all_text)
        return text
