import json
import re
from typing import Dict, List

import scrapy

from crawler.core_carrier.base_spiders import BaseCarrierSpider
from crawler.core_carrier.request_helpers import RequestOption
from crawler.core_carrier.rules import RuleManager, BaseRoutingRule
from crawler.core_carrier.items import (
    BaseCarrierItem, MblItem, LocationItem, VesselItem, ContainerItem, ContainerStatusItem, DebugItem)
from crawler.core_carrier.exceptions import CarrierResponseFormatError, CarrierInvalidMblNoError
from crawler.extractors.table_extractors import TableExtractor, HeaderMismatchError, BaseTableLocator

SITC_BASE_URL = 'http://www.sitcline.com/track/biz/trackCargoTrack.do'


class CarrierSitcSpider(BaseCarrierSpider):
    name = 'carrier_sitc'

    def __init__(self, *args, **kwargs):
        super(CarrierSitcSpider, self).__init__(*args, **kwargs)

        rules = [
            BasicInfoRoutingRule(),
            VesselInfoRoutingRule(),
            ContainerInfoRoutingRule(),
            ContainerStatusRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)

    def start(self):
        request_option = BasicInfoRoutingRule.build_request_option(
            mbl_no=self.mbl_no, container_no_list=self.container_no_list,
        )
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
            **option.meta
        }

        if option.rule_name == RequestOption.METHOD_GET:
            return scrapy.Request(
                url=option.url,
                meta=meta,
            )
        elif option.rule_name == RequestOption.METHOD_POST_FORM:
            return scrapy.FormRequest(
                url=option.url,
                formdata=option.form_data,
                meta=meta,
            )
        else:
            raise RuntimeError()


# -------------------------------------------------------------------------------


class BasicInfoRoutingRule(BaseRoutingRule):
    name = 'BASIC_INFO'

    @classmethod
    def build_request_option(cls, mbl_no, container_no_list) -> RequestOption:
        container_no, other_container_no_list = container_no_list[0], container_no_list[1:]

        form_data = {
            'blNo': mbl_no,
            'containerNo': container_no,
            'queryInfo': '{"queryObjectName": "com.sitc.track.bean.BlNoBkContainer4Track"}'
        }

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_POST_FORM,
            url=f'{SITC_BASE_URL}?method=billNoIndexBasicNew',
            form_data=form_data,
            meta={'mbl_no': mbl_no, 'container_no': container_no, 'container_no_list': other_container_no_list},
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.json'

    def handle(self, response):
        mbl_no = response.meta['mbl_no']
        container_no = response.meta['container_no']
        container_no_list = response.meta['container_no_list']

        response_dict = json.loads(response.text)
        if self._check_valid_mbl(response=response_dict):
            basic_info = self._extract_basic_info(response=response_dict)

            yield MblItem(
                mbl_no=basic_info['mbl_no'],
                pol=LocationItem(name=basic_info['pol_name']),
                final_dest=LocationItem(name=basic_info['final_dest_name']),
            )

            yield VesselInfoRoutingRule.build_request_option(mbl_no=mbl_no, container_no=container_no)

        elif container_no_list:
            yield BasicInfoRoutingRule.build_request_option(mbl_no=mbl_no, container_no_list=container_no_list)

        else:
            raise CarrierInvalidMblNoError()

    @staticmethod
    def _check_valid_mbl(response: Dict):
        data_list = response['list']
        return bool(data_list)

    @staticmethod
    def _extract_basic_info(response: Dict) -> Dict:
        basic_list = response['list']

        if len(basic_list) != 1:
            raise CarrierResponseFormatError(reason=f'basic info length != 1 length: {len(basic_list)}')

        basic_info = basic_list[0]

        return {
            'mbl_no': basic_info['blNo'],
            'pol_name': basic_info['pol'],
            'final_dest_name': basic_info['del'],
        }


class VesselInfoRoutingRule(BaseRoutingRule):
    name = 'VESSEL_INFO'

    @classmethod
    def build_request_option(cls, mbl_no: str, container_no: str) -> RequestOption:
        form_data = {
            'blNo': mbl_no,
            'containerNo': container_no,
            'queryInfo': '{"queryObjectName": "com.sitc.track.bean.BlNoBkContainer4Track"}'
        }

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_POST_FORM,
            url=f'{SITC_BASE_URL}?method=billNoIndexSailingNew',
            form_data=form_data,
            meta={'mbl_no': mbl_no, 'container_no': container_no},
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.json'

    def handle(self, response):
        mbl_no = response.meta['mbl_no']
        container_no = response.meta['container_no']

        response_dict = json.loads(response.text)
        vessel_info_list = self._extract_vessel_info_list(response=response_dict)

        for vessel in vessel_info_list:
            vessel_no = vessel['vessel']
            yield VesselItem(
                vessel_key=vessel_no,
                vessel=vessel_no,
                voyage=vessel['voyage'],
                pol=LocationItem(name=vessel['pol_name']),
                pod=LocationItem(name=vessel['pod_name']),
                etd=vessel['etd'] or None,
                atd=vessel['atd'] or None,
                eta=vessel['eta'] or None,
                ata=vessel['ata'] or None,
            )

        yield ContainerInfoRoutingRule.build_request_option(mbl_no=mbl_no, container_no=container_no)

    def _extract_vessel_info_list(self, response: Dict) -> List:
        vessel_list = response['list']

        return_list = []
        for vessel in vessel_list:
            td = self._extract_estimate_and_actual_time(vessel_time=vessel['atd'])
            ta = self._extract_estimate_and_actual_time(vessel_time=vessel['ata'])

            return_list.append({
                'vessel': vessel['vesselName'],
                'voyage': vessel['voyage'],
                'pol_name': vessel['portFrom'],
                'pod_name': vessel['portTo'],
                'etd': td['e_time'],
                'atd': td['a_time'],
                'eta': ta['e_time'],
                'ata': ta['a_time'],
            })

        return return_list

    @staticmethod
    def _extract_estimate_and_actual_time(vessel_time) -> Dict:
        patt = re.compile(r'^<font color="(?P<e_or_a>\w+)">(?P<local_date_time>\d{4}-\d{2}-\d{2} \d{2}:\d{2})</font>$')
        m = patt.match(vessel_time)
        if not m:
            raise CarrierResponseFormatError(reason=f'time not match, vessel_time: {vessel_time}')

        e_or_a = m.group('e_or_a')
        local_date_time = m.group('local_date_time')

        if e_or_a == 'red':
            return {
                'e_time': '',
                'a_time': local_date_time,
            }

        elif e_or_a == 'black':
            return {
                'e_time': local_date_time,
                'a_time': '',
            }

        else:
            raise CarrierResponseFormatError(reason=f'unknown e_or_a: `{e_or_a}`')


class ContainerInfoRoutingRule(BaseRoutingRule):
    name = 'CONTAINER_INFO'

    @classmethod
    def build_request_option(cls, mbl_no: str, container_no: str) -> RequestOption:
        form_data = {
            'blNo': mbl_no,
            'containerNo': container_no,
            'queryInfo': '{"queryObjectName": "com.sitc.track.bean.BlNoBkContainer4Track"}'
        }

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_POST_FORM,
            url=f'{SITC_BASE_URL}?method=billNoIndexContainersNew',
            form_data=form_data,
            meta={'mbl_no': mbl_no},
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.json'

    def handle(self, response):
        mbl_no = response.meta['mbl_no']

        response_dict = json.loads(response.text)
        container_info_list = self._extract_container_info_list(response=response_dict)

        for container in container_info_list:
            container_no = container['container_no']
            yield ContainerItem(
                container_key=container_no,
                container_no=container_no,
            )

            yield ContainerStatusRoutingRule.build_request_option(mbl_no=mbl_no, container_no=container_no)

    @staticmethod
    def _extract_container_info_list(response: Dict) -> List:
        container_list = response['list']

        return_list = []
        for container in container_list:
            return_list.append({
                'container_no': container['containerNo'],
            })

        return return_list


class ContainerStatusRoutingRule(BaseRoutingRule):
    name = 'CONTAINER_STATUS'

    @classmethod
    def build_request_option(cls, mbl_no: str, container_no: str) -> RequestOption:
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=f'{SITC_BASE_URL}?method=boxNoIndex&containerNo={container_no}&blNo={mbl_no}',
            meta={'container_key': container_no}
        )

    def get_save_name(self, response) -> str:
        container_key = response.meta['container_key']
        return f'{self.name}_{container_key}.html'

    def handle(self, response):
        container_key = response.meta['container_key']

        container_status_list = self._extract_container_status_list(response=response)
        for container_status in container_status_list:
            yield ContainerStatusItem(
                container_key=container_key,
                description=container_status['description'],
                local_date_time=container_status['local_date_time'],
                location=LocationItem(name=container_status['location_name'])
            )

    @staticmethod
    def _extract_container_status_list(response: scrapy.Selector) -> List:
        table_selector = response.css('table#tblCargoTrackBillNo_table')

        if table_selector is None:
            raise CarrierResponseFormatError(reason='Container Status table not found')

        table_locator = ContainerStatusTableLocator()
        table_locator.parse(table=table_selector)
        table = TableExtractor(table_locator=table_locator)

        container_status_list = []
        for left in table_locator.iter_left_headers():
            container_status_list.append({
                'local_date_time': table.extract_cell('Occurrence Time', left),
                'description': table.extract_cell('Current Status', left),
                'location_name': table.extract_cell('Locale', left),
            })

        return container_status_list


class ContainerStatusTableLocator(BaseTableLocator):

    TR_TITLE_INDEX = 0

    def __init__(self):
        self._td_map = {}
        self._data_len = 0

    def parse(self, table: scrapy.Selector):
        title_tr = table.css('thead tr')[self.TR_TITLE_INDEX]
        data_tr_list = table.css('tbody tr')

        title_text_list = title_tr.css('td::text').getall()

        for title_index, title_text in enumerate(title_text_list):
            data_index = title_index

            title_text = title_text.strip()
            self._td_map[title_text] = []

            for data_tr in data_tr_list:
                data_td = data_tr.css('td')[data_index]

                self._td_map[title_text].append(data_td)

        first_title_text = title_text_list[0]
        self._data_len = len(self._td_map[first_title_text])

    def get_cell(self, top, left) -> scrapy.Selector:
        try:
            return self._td_map[top][left]
        except KeyError as err:
            raise HeaderMismatchError(repr(err))

    def has_header(self, top=None, left=None) -> bool:
        return (top in self._td_map) and (left is None)

    def iter_left_headers(self):
        for index in range(self._data_len):
            yield index

