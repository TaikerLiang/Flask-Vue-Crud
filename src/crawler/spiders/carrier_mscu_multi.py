import re
from typing import List, Dict

import scrapy

from crawler.core_carrier.base import SHIPMENT_TYPE_MBL, SHIPMENT_TYPE_BOOKING
from crawler.core_carrier.base_spiders import BaseMultiCarrierSpider
from crawler.core_carrier.exceptions import (
    LoadWebsiteTimeOutError, CarrierResponseFormatError, CarrierInvalidMblNoError, SuspiciousOperationError,
    CarrierInvalidSearchNoError)
from crawler.core_carrier.items import (
    ContainerItem,
    ContainerStatusItem,
    LocationItem,
    MblItem,
    DebugItem,
    BaseCarrierItem,
)
from crawler.core_carrier.request_helpers import RequestOption, ProxyManager
from crawler.core_carrier.rules import BaseRoutingRule, RuleManager
from crawler.extractors.table_cell_extractors import FirstTextTdExtractor
from crawler.extractors.table_extractors import BaseTableLocator, HeaderMismatchError, TableExtractor

URL = 'https://www.msc.com'


class CarrierMscuSpider(BaseMultiCarrierSpider):
    name = 'carrier_mscu_multi'

    def __init__(self, *args, **kwargs):
        super(CarrierMscuSpider, self).__init__(*args, **kwargs)

        self.custom_settings.update({'CONCURRENT_REQUESTS': '1'})

        bill_rules = [
            HomePageRoutingRule(),
            MainRoutingRule(search_type=SHIPMENT_TYPE_MBL),
        ]

        booking_rules = [
            HomePageRoutingRule(),
            MainRoutingRule(search_type=SHIPMENT_TYPE_BOOKING),
        ]

        if self.search_type == SHIPMENT_TYPE_MBL:
            self._rule_manager = RuleManager(rules=bill_rules)
        elif self.search_type == SHIPMENT_TYPE_BOOKING:
            self._rule_manager = RuleManager(rules=booking_rules)

        self._proxy_manager = ProxyManager(session='mscu', logger=self.logger)

    def start(self):
        for s_no, t_id in zip(self.search_nos, self.task_ids):
            option = self._prepare_start(search_no=s_no, task_id=t_id)
            yield self._build_request_by(option=option)

    def _prepare_start(self, search_no: str, task_id: str):
        self._proxy_manager.renew_proxy()
        option = HomePageRoutingRule.build_request_option(search_no=search_no, task_id=task_id)
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
                dont_filter=True,
            )

        elif option.method == RequestOption.METHOD_POST_FORM:
            return scrapy.FormRequest(
                url=option.url,
                formdata=option.form_data,
                meta=meta,
                dont_filter=True,
            )
        else:
            raise SuspiciousOperationError(msg=f'Unexpected request method: `{option.method}`')


# -------------------------------------------------------------------------------


class HomePageRoutingRule(BaseRoutingRule):
    name = 'HOME_PAGE'

    @classmethod
    def build_request_option(cls, search_no, task_id) -> RequestOption:
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url='https://www.msc.com/track-a-shipment?agencyPath=twn',
            meta={
                'search_no': search_no,
                'task_id': task_id,
            },
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.html'

    def handle(self, response):
        task_id = response.meta['task_id']
        search_no = response.meta['search_no']

        view_state = response.css('input#__VIEWSTATE::attr(value)').get()
        validation = response.css('input#__EVENTVALIDATION::attr(value)').get()

        yield MainRoutingRule.build_request_option(
            search_no=search_no, view_state=view_state, validation=validation, task_id=task_id)


# -------------------------------------------------------------------------------


class MainRoutingRule(BaseRoutingRule):
    name = 'MAIN'

    def __init__(self, search_type):
        self._search_type = search_type

    @classmethod
    def build_request_option(cls, search_no, view_state, validation, task_id) -> RequestOption:
        form_data = {
            '__EVENTTARGET': 'ctl00$ctl00$plcMain$plcMain$TrackSearch$hlkSearch',
            '__EVENTVALIDATION': validation,
            '__VIEWSTATE': view_state,
            'ctl00$ctl00$plcMain$plcMain$TrackSearch$txtBolSearch$TextField': search_no,
        }

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_POST_FORM,
            form_data=form_data,
            url='https://www.msc.com/track-a-shipment?agencyPath=twn',
            meta={
                'search_no': search_no,
                'task_id': task_id,
            }
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.html'

    def handle(self, response):
        if self._is_search_no_invalid(response=response):
            raise CarrierInvalidSearchNoError(search_type=self._search_type)

        task_id = response.meta['task_id']
        search_no = response.meta['search_no']
        extractor = Extractor()

        place_of_deliv_set = set()
        container_selector_map_list = extractor.locate_container_selector(response=response)
        for container_selector_map in container_selector_map_list:
            container_no = extractor.extract_container_no(container_selector_map)

            yield ContainerItem(
                task_id=task_id,
                container_key=container_no,
                container_no=container_no,
            )

            container_status_list = extractor.extract_container_status_list(container_selector_map)
            for container_status in container_status_list:
                yield ContainerStatusItem(
                    task_id=task_id,
                    container_key=container_no,
                    description=container_status['description'],
                    local_date_time=container_status['local_date_time'],
                    location=LocationItem(name=container_status['location']),
                    vessel=container_status['vessel'] or None,
                    voyage=container_status['voyage'] or None,
                    est_or_actual=container_status['est_or_actual'],
                )

            place_of_deliv = extractor.extract_place_of_deliv(container_selector_map)
            place_of_deliv_set.add(place_of_deliv)

        if not place_of_deliv_set:
            place_of_deliv = None
        elif len(place_of_deliv_set) == 1:
            place_of_deliv = list(place_of_deliv_set)[0] or None
        else:
            raise CarrierResponseFormatError(reason=f'Different place_of_deliv: `{place_of_deliv_set}`')

        search_no = extractor.extract_search_no(response=response)
        main_info = extractor.extract_main_info(response=response)
        latest_update = extractor.extract_latest_update(response=response)

        mbl_item = MblItem(
            task_id=task_id,
            pol=LocationItem(name=main_info['pol']),
            pod=LocationItem(name=main_info['pod']),
            etd=main_info['etd'],
            vessel=main_info['vessel'],
            place_of_deliv=LocationItem(name=place_of_deliv),
            latest_update=latest_update,
        )
        if self._search_type == SHIPMENT_TYPE_MBL:
            mbl_item['mbl_no'] = search_no
        else:
            mbl_item['booking_no'] = search_no
        yield mbl_item

    @staticmethod
    def _is_search_no_invalid(response: scrapy.Selector):
        error_message = response.css('div#ctl00_ctl00_plcMain_plcMain_pnlTrackingResults > h3::text').get()
        if error_message == 'No matching tracking information. Please try again.':
            return True
        return False


# -------------------------------------------------------------------------------


class Extractor:
    def __init__(self):
        self._mbl_no_pattern = re.compile(r'^Bill of lading: (?P<mbl_no>\S+) ([(]\d+ containers?[)])?$')
        self._container_no_pattern = re.compile(r'^Container: (?P<container_no>\S+)$')
        self._latest_update_pattern = re.compile(r'^Tracking results provided by MSC on (?P<latest_update>.+)$')

    def extract_search_no(self, response: scrapy.Selector):
        search_no_text = response.css('a#ctl00_ctl00_plcMain_plcMain_rptBOL_ctl00_hlkBOLToggle::text').get()

        if not search_no_text:
            return None

        return self._parse_mbl_no(search_no_text)

    def _parse_mbl_no(self, mbl_no_text: str):
        """
        Sample Text:
            `Bill of lading: MEDUN4194175 (1 container)`
            `Bill of lading: MEDUH3870035 `
        """
        m = self._mbl_no_pattern.match(mbl_no_text)
        if not m:
            raise CarrierResponseFormatError(reason=f'Unknown mbl no format: `{mbl_no_text}`')

        return m.group('mbl_no')

    @staticmethod
    def extract_main_info(response: scrapy.Selector):
        main_outer = response.css('div#ctl00_ctl00_plcMain_plcMain_rptBOL_ctl00_pnlBOLContent')
        error_message = (
            'Can not find main information frame by css `div#ctl00_ctl00_plcMain_plcMain_rptBOL_ctl00' '_pnlBOLContent`'
        )
        if not main_outer:
            raise CarrierResponseFormatError(reason=error_message)

        table_selector = main_outer.xpath('./table[@class="resultTable singleRowTable"]')
        if not table_selector:
            return {
                'pol': None,
                'pod': None,
                'etd': None,
                'vessel': None,
            }

        table_locator = MainInfoTableLocator()
        table_locator.parse(table=table_selector)
        table_extractor = TableExtractor(table_locator=table_locator)
        td_extractor = FirstTextTdExtractor()

        return {
            'pol': table_extractor.extract_cell(top='Port of load', left=None, extractor=td_extractor),
            'pod': table_extractor.extract_cell(top='Port of discharge', left=None, extractor=td_extractor),
            'etd': table_extractor.extract_cell(top='Departure date', left=None, extractor=td_extractor),
            'vessel': table_extractor.extract_cell(top='Vessel', left=None, extractor=td_extractor),
        }

    @staticmethod
    def locate_container_selector(response) -> List[Dict]:
        container_content_list = response.css('dl.containerAccordion dd')
        map_list = []

        for container_content in container_content_list:
            container_no_bar = container_content.css('a.containerToggle')
            if not container_no_bar:
                raise CarrierResponseFormatError(reason='Can not find container_no_bar !!!')

            container_stats_table = container_content.css('table.singleRowTable')

            if not container_stats_table:
                raise CarrierResponseFormatError(reason='Can not find container_stats_table !!!')

            movements_table = container_content.css("table[class='resultTable']")
            if not movements_table:
                raise CarrierResponseFormatError(reason='Can not find movements_table !!!')

            map_list.append(
                {
                    'container_no_bar': container_no_bar,
                    'container_stats_table': container_stats_table,
                    'movements_table': movements_table,
                }
            )

        return map_list

    def extract_container_no(self, container_selector_map: Dict[str, scrapy.Selector]):
        container_no_bar = container_selector_map['container_no_bar']

        container_no_text = container_no_bar.css('::text').get()

        return self._parse_container_no(container_no_text)

    def _parse_container_no(self, container_no_text):
        """
        Sample Text:
            Container: GLDU7636572
        """
        m = self._container_no_pattern.match(container_no_text)

        if not m:
            raise CarrierResponseFormatError(reason=f'Unknown container no format: `{container_no_text}`')

        return m.group('container_no')

    @staticmethod
    def extract_place_of_deliv(container_selector_map: Dict[str, scrapy.Selector]):
        table_selector = container_selector_map['container_stats_table']

        table_locator = ContainerInfoTableLocator()
        table_locator.parse(table=table_selector)
        table_extractor = TableExtractor(table_locator=table_locator)
        td_extractor = FirstTextTdExtractor()

        return table_extractor.extract_cell(top='Shipped to', left=None, extractor=td_extractor)

    @staticmethod
    def extract_container_status_list(container_selector_map: Dict[str, scrapy.Selector]):
        table_selector = container_selector_map['movements_table']

        table_locator = ContainerStatusTableLocator()
        table_locator.parse(table=table_selector)
        table_extractor = TableExtractor(table_locator=table_locator)
        td_extractor = FirstTextTdExtractor()

        container_status_list = []
        for left in table_locator.iter_left_header():
            schedule_status = table_extractor.extract_cell(top=table_locator.STATUS_TOP, left=left)

            if schedule_status == 'past':
                est_or_actual = 'A'
            elif schedule_status == 'future':
                est_or_actual = 'E'
            else:
                raise CarrierResponseFormatError(reason=f'Unknown schedule_status: `{schedule_status}`')

            container_status_list.append(
                {
                    'location': table_extractor.extract_cell(top='Location', left=left, extractor=td_extractor),
                    'local_date_time': table_extractor.extract_cell(top='Date', left=left, extractor=td_extractor),
                    'description': table_extractor.extract_cell(top='Description', left=left, extractor=td_extractor),
                    'vessel': table_extractor.extract_cell(top='Vessel', left=left, extractor=td_extractor),
                    'voyage': table_extractor.extract_cell(top='Voyage', left=left, extractor=td_extractor),
                    'est_or_actual': est_or_actual,
                }
            )

        return container_status_list

    def extract_latest_update(self, response: scrapy.Selector):
        latest_update_message = response.css('div#ctl00_ctl00_plcMain_plcMain_pnlTrackingResults > p::text').get()
        return self._parse_latest_update(latest_update_message)

    def _parse_latest_update(self, latest_update_message: str):
        """
        Sample Text:
            Tracking results provided by MSC on 05.11.2019 at 10:50 W. Europe Standard Time
        """
        m = self._latest_update_pattern.match(latest_update_message)
        if not m:
            raise CarrierResponseFormatError(reason=f'Unknown latest update message format: `{latest_update_message}`')

        return m.group('latest_update').strip()


class MainInfoTableLocator(BaseTableLocator):
    """
    +-----------+-----------+-----+-----------+ <thead>      -+
    | Title A-1 | Title A-2 | ... | Title A-N | <tr> <th>     |
    +-----------+-----------+-----+-----------+ <tbody>       | A
    | Cell A-1  | Cell A-2  | ... | Cell A-N  | <tr> <td>     |
    +-----------+-----------+-----+-----------+ <thead>      -+
    | Title B-1 | Title B-2 | ... | Title B-N | <tr> <th>     |
    +-----------+-----------+-----+-----------+ <tbody>       | B
    | Cell B-1  | Cell B-2  | ... | Cell B-N  | <tr> <td>     |
    +-----------+-----------+-----+-----------+              -+
    """

    def __init__(self):
        self._td_map = {}  # top_header: td

    def parse(self, table: scrapy.Selector):
        thead_list = table.css('thead')
        tbody_list = table.css('tbody')

        for thead_index, thead in enumerate(thead_list):
            tbody_index = thead_index
            tbody = tbody_list[tbody_index]

            th_list = thead.css('tr th')
            td_list = tbody.css('tr td')

            for th_index, th in enumerate(th_list):
                td_index = th_index
                td = td_list[td_index]

                top = self._extract_top(th=th)
                self._td_map[top] = td

    @staticmethod
    def _extract_top(th):
        th_text = th.css('::text').get()
        return th_text.strip() if isinstance(th_text, str) else ''

    def get_cell(self, top, left) -> scrapy.Selector:
        assert left is None
        try:
            return self._td_map[top]
        except (KeyError, IndexError) as err:
            raise HeaderMismatchError(repr(err))

    def has_header(self, top=None, left=None) -> bool:
        return (top in self._td_map) and (left is None)


class ContainerInfoTableLocator(BaseTableLocator):
    """
    +-----------+-----------+-----+-----------+ <tbody>      -+
    | Title A-1 | Title A-2 | ... | Title A-N | <tr> <th>     |
    +-----------+-----------+-----+-----------+               | A
    | Cell A-1  | Cell A-2  | ... | Cell A-N  | <tr> <td>     |
    +-----------+-----------+-----+-----------+              -+
    | Title B-1 | Title B-2 | ... | Title B-N | <tr> <th>     |
    +-----------+-----------+-----+-----------+               | B
    | Cell B-1  | Cell B-2  | ... | Cell B-N  | <tr> <td>     |
    +-----------+-----------+-----+-----------+ <\tbody>     -+
    """

    def __init__(self):
        self._td_map = {}  # top_header: td

    def parse(self, table: scrapy.Selector):
        th_row_list = table.xpath('.//th/parent::tr')
        td_row_list = table.xpath('.//td/parent::tr')

        for th_row_index, th_row in enumerate(th_row_list):
            td_row_index = th_row_index
            td_row = td_row_list[td_row_index]

            th_list = th_row.css('th')
            td_list = td_row.css('td')

            for th_index, th in enumerate(th_list):
                td_index = th_index
                td = td_list[td_index]

                top = self._extract_top(th=th)
                self._td_map[top] = td

    @staticmethod
    def _extract_top(th):
        th_text = th.css('::text').get()
        return th_text.strip() if isinstance(th_text, str) else ''

    def get_cell(self, top, left) -> scrapy.Selector:
        assert left is None
        try:
            return self._td_map[top]
        except (KeyError, IndexError) as err:
            raise HeaderMismatchError(repr(err))

    def has_header(self, top=None, left=None) -> bool:
        return (top in self._td_map) and (left is None)


class ContainerStatusTableLocator(BaseTableLocator):

    STATUS_TOP = 'STATUS'

    def __init__(self):
        self._td_map = {}  # top_header: [td, ...]
        self._data_len = 0

    def parse(self, table: scrapy.Selector):
        th_list = table.css('thead th')
        data_tr_list = table.css('tbody tr')

        for th_index, th in enumerate(th_list):
            top_header = self._extract_top_header(th=th)
            self._td_map[top_header] = []

            data_index = th_index
            for data_tr in data_tr_list:
                data_td = data_tr.css('td')[data_index]
                self._td_map[top_header].append(data_td)

        tr_class_name_list = [data_tr.css('::attr(class)').get() for data_tr in data_tr_list]
        status_td_list = [scrapy.Selector(text=f'<td>{tr_class_name}</td>') for tr_class_name in tr_class_name_list]
        self._td_map[self.STATUS_TOP] = status_td_list

        self._data_len = len(data_tr_list)

    @staticmethod
    def _extract_top_header(th):
        top_header = th.css('::text').get()
        return top_header.strip() if isinstance(top_header, str) else ''

    def get_cell(self, top, left) -> scrapy.Selector:
        try:
            return self._td_map[top][left]
        except (KeyError, IndexError) as err:
            raise HeaderMismatchError(repr(err))

    def has_header(self, top=None, left=None) -> bool:
        return (top in self._td_map) and (left is None)

    def iter_left_header(self):
        for i in range(self._data_len):
            yield i
