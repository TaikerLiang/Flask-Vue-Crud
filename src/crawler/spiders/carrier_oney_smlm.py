import json
import time
from typing import List

import scrapy

from crawler.core_carrier.base_spiders import BaseCarrierSpider
from crawler.core_carrier.exceptions import CarrierResponseFormatError, CarrierInvalidMblNoError
from crawler.core_carrier.items import (
    BaseCarrierItem, VesselItem, ContainerStatusItem, LocationItem, ContainerItem, MblItem, DebugItem)
from crawler.core_carrier.rules import RuleManager, RoutingRequest, BaseRoutingRule


class SharedSpider(BaseCarrierSpider):
    name = None
    base_url = None

    def __init__(self, *args, **kwargs):
        super(SharedSpider, self).__init__(*args, **kwargs)

        rules = [
            FirstTierRoutingRule(base_url=self.base_url),
            VesselRoutingRule(),
            ContainerStatusRoutingRule(),
            ReleaseStatusRoutingRule(),
            RailInfoRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)

    def start(self):
        routing_request = FirstTierRoutingRule.build_routing_request(mbl_no=self.mbl_no, base_url=self.base_url)
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
                yield self._rule_manager.build_request_by(routing_request=result)
            else:
                raise RuntimeError()


class CarrierOneySpider(SharedSpider):
    name = 'carrier_oney'
    base_url = 'https://ecomm.one-line.com/ecom/CUP_HOM_3301GS.do'


class CarrierSmlmSpider(SharedSpider):
    name = 'carrier_smlm'
    base_url = 'https://esvc.smlines.com/smline/CUP_HOM_3301GS.do'


# -----------------------------------------------------------------------------------------------------------


class FirstTierRoutingRule(BaseRoutingRule):
    name = 'FIRST_TIER'
    f_cmd = '121'

    def __init__(self, base_url):
        # aim to build other routing_request
        self.base_url = base_url

    @classmethod
    def build_routing_request(cls, mbl_no, base_url) -> RoutingRequest:
        time_stamp = build_timestamp()

        url = (
            f'{base_url}?_search=false&nd={time_stamp}&rows=10000&page=1&sidx=&sord=asc&'
            f'f_cmd={cls.f_cmd}&search_type=B&search_name={mbl_no}&cust_cd='
        )
        request = scrapy.Request(url=url)

        return RoutingRequest(request=request, rule_name=cls.name)

    def get_save_name(self, response) -> str:
        return f'{self.name}.json'

    def handle(self, response):
        response_dict = json.loads(response.text)

        if not self._check_mbl_no(response_dict):
            raise CarrierInvalidMblNoError()

        container_info_list = self._extract_container_info_list(response_dict=response_dict)
        booking_no = self._get_booking_no_from(container_list=container_info_list)
        mbl_no = self._get_mbl_no_from(container_list=container_info_list)

        yield MblItem(
            mbl_no=mbl_no
        )

        yield VesselRoutingRule.build_routing_request(booking_no=booking_no, base_url=self.base_url)

        for container_info in container_info_list:
            container_no = container_info['container_no']

            yield ContainerItem(
                container_key=container_no,
                container_no=container_no,
            )

            yield ContainerStatusRoutingRule.build_routing_request(
                container_no=container_no,
                booking_no=container_info['booking_no'],
                cooperation_no=container_info['cooperation_no'],
                base_url=self.base_url,
            )

            yield ReleaseStatusRoutingRule.build_routing_request(
                container_no=container_no,
                booking_no=booking_no,
                base_url=self.base_url,
            )

            yield RailInfoRoutingRule.build_routing_request(
                container_no=container_no,
                cooperation=container_info['cooperation_no'],
                base_url=self.base_url,
            )

    @staticmethod
    def _check_mbl_no(response_dict):
        return 'list' in response_dict

    @staticmethod
    def _extract_container_info_list(response_dict) -> List:
        container_data_list = response_dict.get('list')
        if not container_data_list:
            raise CarrierResponseFormatError(reason=f'Can not find container_data: `{response_dict}`')

        container_info_list = []
        for container_data in container_data_list:
            mbl_no = container_data['blNo'].strip()
            container_no = container_data['cntrNo'].strip()
            booking_no = container_data['bkgNo'].strip()
            cooperation_no = container_data['copNo'].strip()

            container_info_list.append({
                'mbl_no': mbl_no,
                'container_no': container_no,
                'booking_no': booking_no,
                'cooperation_no': cooperation_no,
            })

        return container_info_list

    @staticmethod
    def _get_booking_no_from(container_list: List):
        booking_no_list = [container['booking_no'] for container in container_list]
        booking_no_set = set(booking_no_list)

        if len(booking_no_set) != 1:
            raise CarrierResponseFormatError(reason=f'All the booking_no are not the same: `{booking_no_set}`')

        return booking_no_list[0]

    @staticmethod
    def _get_mbl_no_from(container_list: List):
        mbl_no_list = [container['mbl_no'] for container in container_list]
        mbl_no_set = set(mbl_no_list)

        if len(mbl_no_set) != 1:
            raise CarrierResponseFormatError(reason=f'All the mbl_no are not the same: `{mbl_no_set}`')

        return mbl_no_list[0]


class VesselRoutingRule(BaseRoutingRule):
    name = 'VESSEL'
    f_cmd = '124'

    @classmethod
    def build_routing_request(cls, booking_no, base_url) -> RoutingRequest:
        formdata = {
            'f_cmd': cls.f_cmd,
            'bkg_no': booking_no,
        }
        request = scrapy.FormRequest(
            url=base_url,
            formdata=formdata,
        )

        return RoutingRequest(request=request, rule_name=cls.name)

    def get_save_name(self, response) -> str:
        return f'{self.name}.json'

    def handle(self, response):
        response_dict = json.loads(response.text)

        vessel_info_list = self._extract_vessel_info_list(response_dict=response_dict)
        for vessel_info in vessel_info_list:
            yield VesselItem(
                vessel_key=vessel_info['name'],
                vessel=vessel_info['name'],
                voyage=vessel_info['voyage'],
                pol=LocationItem(name=vessel_info['pol']),
                pod=LocationItem(name=vessel_info['pod']),
                etd=vessel_info['etd'],
                atd=vessel_info['atd'],
                eta=vessel_info['eta'],
                ata=vessel_info['ata'],
            )

    @staticmethod
    def _extract_vessel_info_list(response_dict) -> List:
        vessel_data_list = response_dict['list']
        vessel_info_list = []
        for vessel_data in vessel_data_list:
            vessel_info_list.append({
                'name': vessel_data['vslEngNm'].strip(),
                'voyage': vessel_data['skdVoyNo'].strip() + vessel_data['skdDirCd'].strip(),
                'pol': vessel_data['polNm'].strip(),
                'pod': vessel_data['podNm'].strip(),
                'etd': vessel_data['etd'].strip() if vessel_data['etdFlag'] == 'C' else None,
                'atd': vessel_data['etd'].strip() if vessel_data['etdFlag'] == 'A' else None,
                'eta': vessel_data['eta'].strip() if vessel_data['etaFlag'] == 'C' else None,
                'ata': vessel_data['eta'].strip() if vessel_data['etaFlag'] == 'A' else None,
            })

        return vessel_info_list


class ContainerStatusRoutingRule(BaseRoutingRule):
    name = 'CONTAINER_STATUS'
    f_cmd = '125'

    @classmethod
    def build_routing_request(cls, container_no, booking_no, cooperation_no, base_url):
        formdata = {
            'f_cmd': cls.f_cmd,
            'cntr_no': container_no,
            'bkg_no': booking_no,
            'cop_no': cooperation_no,
        }
        request = scrapy.FormRequest(
            url=base_url,
            formdata=formdata,
            meta={'container_key': container_no},
        )

        return RoutingRequest(request=request, rule_name=cls.name)

    def get_save_name(self, response) -> str:
        container_key = response.meta['container_key']
        return f'{self.name}_{container_key}.json'

    def handle(self, response):
        container_key = response.meta['container_key']
        response_dict = json.loads(response.text)

        container_status_list = self._extract_container_status_list(response_dict=response_dict)

        for container_status in container_status_list:
            yield ContainerStatusItem(
                container_key=container_key,
                description=container_status['status'],
                local_date_time=container_status['local_time'],
                location=LocationItem(name=container_status['location']),
                est_or_actual=container_status['est_or_actual'],
            )

    @staticmethod
    def _extract_container_status_list(response_dict):
        if 'list' not in response_dict:
            return []

        container_status_data_list = response_dict['list']
        container_status_info_list = []
        for container_status_data in container_status_data_list:
            local_time = container_status_data['eventDt'].strip()
            if not local_time:
                # time is empty --> ignore this event
                continue

            status_with_br = container_status_data['statusNm'].strip()
            status = status_with_br.replace('<br>', ' ')

            container_status_info_list.append({
                'status': status,
                'location': container_status_data['placeNm'].strip(),
                'local_time': local_time,
                'est_or_actual': container_status_data['actTpCd'].strip(),
            })

        return container_status_info_list


class ReleaseStatusRoutingRule(BaseRoutingRule):
    name = 'RELEASE_STATUS'
    f_cmd = '126'

    @classmethod
    def build_routing_request(cls, container_no, booking_no, base_url) -> RoutingRequest:
        formdata = {
            'f_cmd': cls.f_cmd,
            'cntr_no': container_no,
            'bkg_no': booking_no,
        }

        request = scrapy.FormRequest(
            url=base_url,
            formdata=formdata,
            meta={'container_key': container_no},
        )
        return RoutingRequest(request=request, rule_name=cls.name)

    def get_save_name(self, response) -> str:
        container_key = response.meta['container_key']
        return f'{self.name}_{container_key}.json'

    def handle(self, response):
        container_key = response.meta['container_key']
        response_dict = json.loads(response.text)

        release_info = self._extract_release_info(response_dict=response_dict)

        yield MblItem(
            freight_date=release_info['freight_date'] or None,
            us_customs_date=release_info['us_customs_date'] or None,
            us_filing_date=release_info['us_filing_date'] or None,
            firms_code=release_info['firms_code'] or None,
        )

        yield ContainerItem(
            container_key=container_key,
            last_free_day=release_info['last_free_day'] or None,
        )

    @staticmethod
    def _extract_release_info(response_dict):
        if 'list' not in response_dict:
            return {
                'freight_date': None,
                'us_customs_date': None,
                'us_filing_date': None,
                'firms_code': None,
                'last_free_day': None,
            }

        release_data_list = response_dict['list']
        if len(release_data_list) != 1:
            raise CarrierResponseFormatError(reason=f'Release information format error: `{release_data_list}`')

        release_data = release_data_list[0]

        return {
            'freight_date': release_data['ocnFrtColDt'],
            'us_customs_date': release_data['cstmsClrDt'],
            'us_filing_date': release_data['impFilDt'],
            'firms_code': release_data['delFirmsCode'],
            'last_free_day': release_data['lastFreeDt'],
        }


class RailInfoRoutingRule(BaseRoutingRule):
    name = 'RAIL_INFORMATION'
    f_cmd = '127'

    @classmethod
    def build_routing_request(cls, container_no, cooperation, base_url) -> RoutingRequest:
        formdata = {
            'f_cmd': cls.f_cmd,
            'cop_no': cooperation,
        }
        request = scrapy.FormRequest(
            url=base_url,
            formdata=formdata,
            meta={'container_key': container_no},
        )

        return RoutingRequest(request=request, rule_name=cls.name)

    def get_save_name(self, response) -> str:
        container_key = response.meta['container_key']
        return f'{self.name}_{container_key}.json'

    def handle(self, response):
        container_key = response.meta['container_key']
        response_dict = json.loads(response.text)

        ready_for_pick_up = self._extract_ready_for_pick_up(response_dict=response_dict)

        yield ContainerItem(
            container_key=container_key,
            ready_for_pick_up=ready_for_pick_up or None,
        )

    @staticmethod
    def _extract_ready_for_pick_up(response_dict):
        if 'list' not in response_dict:
            return None

        rail_data_list = response_dict['list']
        if len(rail_data_list) >= 2:
            raise CarrierResponseFormatError(f'Rail information format error: `{rail_data_list}`')

        return rail_data_list[0]['pickUpAvail']


# -----------------------------------------------------------------------------------------------------------


def build_timestamp():
    return int(time.time() * 1000)
