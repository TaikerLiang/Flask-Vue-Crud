import abc
from typing import List
import scrapy
from scrapy import Selector

from crawler.core_carrier.base_spiders import BaseCarrierSpider
from crawler.core_carrier.rules import RuleManager, RoutingRequest, BaseRoutingRule
from crawler.core_carrier.items import (
    BaseCarrierItem, MblItem, LocationItem, VesselItem, ContainerItem, ContainerStatusItem)
from crawler.core_carrier.exceptions import CarrierResponseFormatError, CarrierInvalidMblNoError
from crawler.extractors.table_extractors import BaseTableLocator, HeaderMismatchError, TableExtractor
from crawler.extractors.table_cell_extractors import BaseTableCellExtractor


class CarrierOoclSpider(BaseCarrierSpider):
    name = 'carrier_oocl'

    def __init__(self, *args, **kwargs):
        super(CarrierOoclSpider, self).__init__(*args, **kwargs)

        rules = [
            CargoTrackingRule(),
            ContainerStatusRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)

    def start_requests(self):
        routing_request = CargoTrackingRule.build_routing_request(mbl_no=self.mbl_no)
        yield self._rule_manager.build_request_by(routing_request=routing_request)

    def parse(self, response):
        routing_rule = self._rule_manager.get_rule_by_response(response=response)

        for result in routing_rule.handle(response=response):
            if isinstance(result, BaseCarrierItem):
                yield result
            elif isinstance(result, RoutingRequest):
                yield self._rule_manager.build_request_by(routing_request=result)
            else:
                raise RuntimeError()


# -------------------------------------------------------------------------------

JSF_TREE_64 = (
    'H4sIAAAAAAAAAK1Sy24TMRQ1UStE1Yd4iWWRQEJiMfMB2TEQmmraSiFFQllEN/bNjNsZ2732QLphx54P4AuqfkG/gB1bfoIta+6Q0Eb'
    'TQXTBxtb1Odfn+Fyf/xCrnsRrS1kEDmSOUXk6BYmeS1doCUFbEw0J8U2gSoaKcA8MZEhPrw4TWzpr0ITeu0ffv+z+/NYRKyNxZyxzXS'
    'jic7E7SlkinkvEC4l4SSK+qUQ3FVtj+adKCvA+iHvpEbyHuACTxczXJmPa+hWtr07ER9EZidvjWjlwy/3RUs/B5Ahl6M5cRQur/yON7'
    'sX5s693P30+6wgxc0KIW762Iap6XeV6c167IJ7XXmbRXOvSdpSHsoh2eOkbV4UdrVQd5ppHIJkPTx26xQ31usY5THRRHExTUBzBflVO'
    'kBqMLV85ZykchmmSA/kGvDGx9vivvdKaANogtcOEU+RpS2yFNy7hFuPr2vfIlnuWH9DENpFvU6gSVufnN1GPBc8O1Utbsjd340h5TCU'
    'YlWpzzL8hs0ObAPFGIOsEXqTLQtutlKRBeXiNkuwPBw3Sg2ukwase+33yD789SyXPPv/9CeqCex639xz232r8MLA2OPcLUlBlC+IDAA'
    'A='
)
JSF_STATE_64 = (
    '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'
)


class CargoTrackingRule(BaseRoutingRule):
    name = 'CARGO_TRACKING'

    @classmethod
    def build_routing_request(cls, mbl_no: str) -> RoutingRequest:
        form_data = {
            'hiddenForm:searchType': 'BL',
            'hiddenForm:billOfLadingNumber': mbl_no,
            'hiddenForm:containerNumber': '',
            'hiddenForm_SUBMIT': '1',
            'hiddenForm:_link_hidden_': 'hiddenForm:goToCargoTrackingBL',
            'jsf_tree_64': JSF_TREE_64,
            'jsf_state_64': JSF_STATE_64,
            'jsf_viewid': '/cargotracking/ct_search_from_other_domain.jsp'

        }
        request = scrapy.FormRequest(
            url=(
                'http://moc.oocl.com/party/cargotracking/ct_search_from_other_domain.jsf?'
                'ANONYMOUS_TOKEN=kFiFirZYfIHjjEVjGlDTMCCOOCL&ENTRY_TYPE=OOCL'
            ),
            formdata=form_data,
            meta={'mbl_no': mbl_no},
        )
        return RoutingRequest(request=request, rule_name=cls.name)

    def handle(self, response):
        self.check_response(response)

        mbl_info = self._extract_mbl_info(response)\

        yield MblItem(
            mbl_no=mbl_info['mbl_no'],
            por=LocationItem(name=mbl_info['por']),
            etd=mbl_info['etd'],
            atd=mbl_info['atd'],
            voyage=mbl_info['voyage'],
            vessel=mbl_info['vessel'],
            pod=LocationItem(name=mbl_info['pod']),
            ata=mbl_info['ata'],
            eta=mbl_info['eta'],
            place_of_deliv=LocationItem(name=mbl_info['place_of_deliv']),
            deliv_ata=mbl_info['deliv_ata'],
            deliv_eta=mbl_info['deliv_eta'],
            final_dest=LocationItem(name=mbl_info['final_dest']),
        )

        container_no_list = self._extract_container_no_list(response)

        jsf_tree_64 = response.css('input[id=jsf_tree_64]::attr(value)').get()
        jsf_state_64 = response.css('input[id=jsf_state_64]::attr(value)').get()
        for container_no in container_no_list:
            yield ContainerStatusRule.build_routing_request(
                mbl_no=mbl_info['mbl_no'],
                container_no=container_no,
                jsf_tree_64=jsf_tree_64,
                jsf_state_64=jsf_state_64,
            )

    @staticmethod
    def check_response(response):
        if response.css('span[class=noRecordBold]'):
            raise CarrierInvalidMblNoError()

    @staticmethod
    def _extract_mbl_info(response: scrapy.Selector):
        search_result_text = response.css('th[class=sectionTable]::text')[0].get()
        mbl_no = search_result_text.split('\n')[1].strip()

        tables = response.css('table')
        clearance_status_splits = tables[12].css('td')[6].get().split('\n')
        customs_release_status = clearance_status_splits[1].strip()
        customs_release_date = clearance_status_splits[2].strip().strip('()')

        routing_table = response.css('table[id=eventListTable]')[0]

        routing_table_locator = RoutingTableLocator()
        routing_table_locator.parse(table=routing_table)
        routing_table_extractor = TableExtractor(table_locator=routing_table_locator)
        cell_extractor = RoutingTableCellExtractor()

        port_of_load = routing_table_extractor.extract_cell('Port of Load', None, cell_extractor)
        xtd_key = 'atd' if 'Actual' in port_of_load[2] else 'etd'
        xtd = port_of_load[1]

        vessel_voyage = routing_table_extractor.extract_cell('Vessel Voyage', None, cell_extractor)

        port_of_discharge = routing_table_extractor.extract_cell('Port of Discharge', None, cell_extractor)
        xta_key = 'ata' if 'Actual' in port_of_discharge[2] else 'eta'
        xta = port_of_discharge[1]

        final_destination_hub = routing_table_extractor.extract_cell('Port of Discharge', None, cell_extractor)
        deliv_xta_key = 'deliv_ata' if 'Actual' in final_destination_hub[2] else 'deliv_eta'
        deliv_xta = final_destination_hub[1]

        destination = routing_table_extractor.extract_cell('Destination', None, cell_extractor)

        return {
            'mbl_no': f'{mbl_no}',
            'customs_release_status': customs_release_status,
            'customs_release_date': customs_release_date,
            'por': routing_table_extractor.extract_cell('Origin', None, cell_extractor)[0],
            'pol': port_of_load[0],
            'atd': xtd if xtd_key == 'atd' else None,
            'etd': xtd if xtd_key == 'etd' else None,
            'voyage': vessel_voyage[0],
            'vessel': vessel_voyage[1],
            'pod': port_of_load[0],
            'ata': xta if xta_key == 'ata' else None,
            'eta': xta if xta_key == 'eta' else None,
            'place_of_deliv': final_destination_hub[0],
            'deliv_ata': deliv_xta if deliv_xta_key == 'deliv_ata' else None,
            'deliv_eta': deliv_xta if deliv_xta_key == 'deliv_eta' else None,
            'final_dest': destination[0],
        }

    @staticmethod
    def _extract_container_no_list(response: scrapy.Selector):
        table = response.css('table[id=summaryTable]')

        container_table_locator = ContainerTableLocator()
        container_table_locator.parse(table=table)
        table_extractor = TableExtractor(table_locator=container_table_locator)

        container_no_list = []
        for left in container_table_locator.iter_left_headers():
            container_no_list.append(table_extractor.extract_cell('Container Number', left).split('-')[0])
        return container_no_list


class RoutingTableLocator(BaseTableLocator):
    """
        +-----------------------------------+ <tbody>
        | Title 1 | Title 2 | ... |   <th>  | <tr>
        +---------+---------+-----+---------+
        | Data    |         |     |   <td>  | <tr>
        +---------+---------+-----+---------+ </tbody>
    """

    TR_TITLE_INDEX = 0
    TR_DATA_INDEX = 1

    def __init__(self):
        self._td_map = {}
        self._data_len = 0

    def parse(self, table: scrapy.Selector):

        title_list = table.css('tr')[self.TR_TITLE_INDEX].css('th::text').getall()
        data_list = table.css('tr')[self.TR_DATA_INDEX].css('td')

        for index, td in enumerate(data_list):
            self._td_map[title_list[index].strip()] = td

        self._data_len = len(title_list)

    def get_cell(self, top, left) -> scrapy.Selector:
        try:
            return self._td_map[top]
        except KeyError as err:
            raise HeaderMismatchError(repr(err))

    def has_header(self, top=None, left=None) -> bool:
        return (top in self._td_map) and (left is None)


class RoutingTableCellExtractor(BaseTableCellExtractor):
    def extract(self, cell: Selector):
        lines = []
        for text in cell.css('::text').getall():
            normalized_text = text.replace('\n', '').replace('\t', '').replace('  ', ' ').strip()
            if normalized_text != '':
                lines.append(normalized_text)
        return lines


class DestinationTableLocator(BaseTableLocator):
    """
        +-----------------------------------+ <tbody>
        | Title 1 | Data 1  |     |         | <tr>
        +---------+---------+-----+---------+
        | Title 2 | Data 2  |     |         | <tr>
        +---------+---------+-----+---------+
        | Title 3 | Data 3  |     |         | <tr>
        +---------+---------+-----+---------+
        | ...     |         |     |         | <tr>
        +---------+---------+-----+---------+
        | Title N | Data N  |     |         | <tr>
        +---------+---------+-----+---------+ </tbody>
    """

    def __init__(self):
        self._td_map = {}

    def parse(self, table: scrapy.Selector):
        for tr in table.css('tr'):
            title = tr.css('td::text').get().strip()
            self._td_map[title] = tr.css('span')

    def get_cell(self, top, left) -> scrapy.Selector:
        try:
            return self._td_map[left]
        except KeyError as err:
            raise HeaderMismatchError(repr(err))

    def has_header(self, top=None, left=None) -> bool:
        return (left in self._td_map) and (top is None)


class ContainerStatusTableLocator(BaseTableLocator):
    """
        +-----------------------------------+ <tbody>
        | Title 1 | Title 2 | ... | Title N | <tr>
        +---------+---------+-----+---------+
        | Data    |         |     |   <th>  | <tr>
        +---------+---------+-----+---------+
        | Data    |         |     |   <td>  | <tr>
        +---------+---------+-----+---------+
        | ...     |         |     |         | <tr>
        +---------+---------+-----+---------+
        | Data    |         |     |         | <tr>
        +---------+---------+-----+---------+ </tbody>
    """

    def __init__(self):
        self._td_map = {}
        self._data_len = 0

    def parse(self, table: scrapy.Selector):
        title_list = table.css('th::text').getall()
        for tr in table.css('tr'):
            for index, td in enumerate(tr.css('td')):
                title = title_list[index].strip()
                if title not in self._td_map:
                    self._td_map[title] = []
                self._td_map[title].append(td)

        first_title_text = title_list[0]
        self._data_len = len(self._td_map[first_title_text])

    def get_cell(self, top, left) -> scrapy.Selector:
        try:
            return self._td_map[top][left]
        except KeyError as err:
            raise HeaderMismatchError(repr(err))

    def has_header(self, top=None, left=None) -> bool:
        return False

    def iter_left_headers(self):
        for index in range(self._data_len):
            yield index


class ContainerTableLocator(BaseTableLocator):
    def __init__(self):
        self._td_map = {}
        self._data_len = 0

    def parse(self, table: scrapy.Selector):
        tr_list = table.css(':scope > tr')
        # ['Container Number ', 'Container Size Type', 'Quantity',
        # 'Gross Weight', 'Verified Gross Mass', 'Latest Event ', 'Final Destination ']
        # insert ['Event', 'Location', 'Time'] into 'Latest Event '
        title_list = []
        for _title in tr_list[0].css('th::text').getall():
            title = _title.strip()
            if title == 'Latest Event':
                title_list += tr_list[1].css('th::text').getall()
            else:
                title_list.append(title)

        for left, tr in enumerate(tr_list[2:]):
            for index, td in enumerate(tr.css(':scope>td')):
                if title_list[index] not in self._td_map:
                    self._td_map[title_list[index]] = []
                self._td_map[title_list[index]].append(td)

        self._data_len = len(self._td_map[title_list[0]])

    def get_cell(self, top, left) -> scrapy.Selector:
        try:
            return self._td_map[top][left]
        except KeyError as err:
            raise HeaderMismatchError(repr(err))

    def has_header(self, top=None, left=None) -> bool:
        return False

    def iter_left_headers(self):
        for index in range(self._data_len):
            yield index


# -------------------------------------------------------------------------------


def get_multipart_body(form_data, boundary):
    body = ''
    for index, key in enumerate(form_data):
        body += (
            f'--{boundary}\r\n'
            f'Content-Disposition: form-data; name="{key}"\r\n'
            f'\r\n'
            f'{form_data[key]}\r\n'
        )
    body += f'--{boundary}--'
    return body


class ContainerStatusRule(BaseRoutingRule):
    name = 'CONTAINER_STATUS'

    @classmethod
    def build_routing_request(cls, mbl_no: str, container_no: str, jsf_tree_64, jsf_state_64) -> RoutingRequest:
        form_data = {
            'form_SUBMIT': '1',
            'currentContainerNumber': container_no,
            'searchCriteriaBillOfLadingNumber': mbl_no,
            'form:_link_hidden_': 'form:link0',
            'jsf_tree_64': jsf_tree_64,
            'jsf_state_64': jsf_state_64,
            'jsf_viewid': '/cargotracking/ct_result_bl.jsp',
        }
        # generate multipart/form-data with boundary
        boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
        body = get_multipart_body(form_data=form_data, boundary=boundary)
        request = scrapy.Request(
            url=(
                'http://moc.oocl.com/party/cargotracking/ct_result_bl.jsf?ANONYMOUS_TOKEN=abc'
            ),
            method='POST',
            body=body,
            headers={'Content-Type': f'multipart/form-data; boundary={boundary}'},
            meta={'mbl_no': mbl_no, 'container_no': container_no},
        )
        return RoutingRequest(request=request, rule_name=cls.name)

    def handle(self, response):
        container_no = response.meta['container_no']

        container_info = self._extract_container_table(response)
        yield ContainerItem(
            container_key=container_no,
            container_no=container_no,
            last_free_day=container_info['last_free_day'],
            det_free_time_exp_date=container_info['det_free_time_exp_date'],
        )

        container_status_list = self._extract_container_status_list(response)
        for container_status in container_status_list:
            yield ContainerStatusItem(
                description=container_status['description'],
                location=LocationItem(name=container_status['location']),
                transport=container_status['transport'],
                local_date_time=container_status['local_date_time'],
            )

    @staticmethod
    def _extract_container_table(response: scrapy.Selector):
        # container_no = response.css('td[class=groupTitle\ fullByDraftCntNumber]::text').get().split('\xa0')[-1].strip()

        destination_table = response.css('div[id=Tab3] table')[-1]

        destination_table_locator = DestinationTableLocator()
        destination_table_locator.parse(table=destination_table)
        destination_table_extractor = TableExtractor(table_locator=destination_table_locator)

        demurrage_last_free_date = destination_table_extractor.extract_cell(None, 'Demurrage Last Free Date:')
        detention_last_free_date = destination_table_extractor.extract_cell(None, 'Detention Last Free Date:')
        return {
            # 'container_no': container_no.split('-')[0],
            'last_free_day': demurrage_last_free_date,
            'det_free_time_exp_date': detention_last_free_date,
        }

    @staticmethod
    def _extract_container_status_list(response: scrapy.Selector):
        container_table = response.css('table[id=eventListTable]')[1]

        container_status_table_locator = ContainerStatusTableLocator()
        container_status_table_locator.parse(table=container_table)
        container_status_table_extractor = TableExtractor(table_locator=container_status_table_locator)

        container_status_list = []
        for left in container_status_table_locator.iter_left_headers():
            container_status_list.append({
                'description': container_status_table_extractor.extract_cell('Event', left),
                'location': container_status_table_extractor.extract_cell('Location', left),
                'transport': container_status_table_extractor.extract_cell('Mode', left),
                'local_date_time': container_status_table_extractor.extract_cell('Time', left),
            })
        return container_status_list
