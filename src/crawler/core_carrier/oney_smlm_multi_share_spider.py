import json
import time
import dataclasses
from typing import List

import scrapy

from crawler.core_carrier.request_helpers import ProxyManager, RequestOption
from crawler.core_carrier.base import SHIPMENT_TYPE_MBL, SHIPMENT_TYPE_BOOKING
from crawler.core_carrier.base_spiders import BaseMultiCarrierSpider
from crawler.core_carrier.exceptions import CarrierResponseFormatError, CarrierInvalidMblNoError, \
    SuspiciousOperationError, CarrierInvalidSearchNoError
from crawler.core_carrier.items import (
    BaseCarrierItem,
    VesselItem,
    ContainerStatusItem,
    LocationItem,
    ContainerItem,
    MblItem,
    DebugItem,
)
from crawler.core_carrier.rules import RuleManager, BaseRoutingRule


@dataclasses.dataclass
class Restart:
    reason: str = ''
    search_no: str = ''
    task_id: str = ''


class OneySmlmSharedSpider(BaseMultiCarrierSpider):
    name = None
    base_url = None

    def __init__(self, *args, **kwargs):
        super(OneySmlmSharedSpider, self).__init__(*args, **kwargs)

        self._proxy_manager = ProxyManager(session='oneysmlm', logger=self.logger)

        bill_rules = [
            FirstTierRoutingRule(search_type=SHIPMENT_TYPE_MBL),
            VesselRoutingRule(),
            ContainerStatusRoutingRule(),
            ReleaseStatusRoutingRule(),
            RailInfoRoutingRule(),
        ]

        booking_rules = [
            FirstTierRoutingRule(search_type=SHIPMENT_TYPE_BOOKING),
            VesselRoutingRule(),
            ContainerStatusRoutingRule(),
            ReleaseStatusRoutingRule(),
            RailInfoRoutingRule(),
        ]

        if self.search_type == SHIPMENT_TYPE_MBL:
            self._rule_manager = RuleManager(rules=bill_rules)
        elif self.search_type == SHIPMENT_TYPE_BOOKING:
            self._rule_manager = RuleManager(rules=booking_rules)

    def start(self):
        for s_no, t_id in zip(self.search_nos, self.task_ids):
            self._proxy_manager.renew_proxy()
            option = FirstTierRoutingRule.build_request_option(search_no=s_no, task_id=t_id, base_url=self.base_url)
            yield self._build_request_by(option=option)

        # option = FirstTierRoutingRule.build_request_option(search_no=self.search_no, base_url=self.base_url)
        # yield self._build_request_by(option=option)

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
            elif isinstance(result, Restart):
                self.logger.warning(f'----- {result.reason}, try new proxy and restart')
                self._proxy_manager.renew_proxy()

                search_no = result.search_no
                task_id = result.task_id

                option = FirstTierRoutingRule.build_request_option(search_no=search_no, task_id=task_id, base_url=self.base_url)
                proxy_option = self._proxy_manager.apply_proxy_to_request_option(option)
                yield self._build_request_by(proxy_option)
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
                headers=option.headers,
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


class FirstTierRoutingRule(BaseRoutingRule):
    name = 'FIRST_TIER'
    f_cmd = '121'

    def __init__(self, search_type):
        # aim to build other routing_request
        self._search_type = search_type

    @classmethod
    def build_request_option(cls, search_no, base_url, task_id) -> RequestOption:
        time_stamp = build_timestamp()

        url = (
            f'{base_url}?_search=false&nd={time_stamp}&rows=10000&page=1&sidx=&sord=asc&'
            f'f_cmd={cls.f_cmd}&search_type=B&search_name={search_no}&cust_cd='
        )

        headers = {
            'authority': 'ecomm.one-line.com',
            'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="90", "Google Chrome";v="90"',
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'x-requested-with': 'XMLHttpRequest',
            'sec-ch-ua-mobile': '?0',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-mode': 'cors',
            'sec-fetch-dest': 'empty',
            'referer': 'https://ecomm.one-line.com/ecom/CUP_HOM_3301.do?sessLocale=en',
            'accept-language': 'en-US,en;q=0.9',
        }

        return RequestOption(
            method=RequestOption.METHOD_GET,
            rule_name=cls.name,
            url=url,
            headers=headers,
            meta={
                'base_url': base_url,
                'task_id': task_id,
                'search_no': search_no,
            }
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.json'

    def handle(self, response):
        task_id = response.meta['task_id']
        search_no = response.meta['search_no']
        base_url = response.meta['base_url']
        response_dict = json.loads(response.text)

        if self._is_search_no_invalid(response_dict):
            yield Restart(reason='IP block', search_no=search_no, task_id=task_id)

        container_info_list = self._extract_container_info_list(response_dict=response_dict)
        booking_no = self._get_booking_no_from(container_list=container_info_list)
        mbl_no = self._get_mbl_no_from(container_list=container_info_list)

        if self._search_type == SHIPMENT_TYPE_MBL:
            yield MblItem(task_id=task_id, mbl_no=mbl_no)
        else:
            yield MblItem(task_id=task_id, booking_no=booking_no)

        yield VesselRoutingRule.build_request_option(booking_no=booking_no, base_url=base_url, task_id=task_id)

        for container_info in container_info_list:
            container_no = container_info['container_no']

            yield ContainerItem(
                task_id=task_id,
                container_key=container_no,
                container_no=container_no,
            )

            yield ContainerStatusRoutingRule.build_request_option(
                container_no=container_no,
                booking_no=container_info['booking_no'],
                cooperation_no=container_info['cooperation_no'],
                base_url=base_url,
                task_id=task_id,
            )

            yield ReleaseStatusRoutingRule.build_request_option(
                container_no=container_no,
                booking_no=booking_no,
                base_url=base_url,
                task_id=task_id,
            )

            yield RailInfoRoutingRule.build_request_option(
                container_no=container_no,
                cooperation=container_info['cooperation_no'],
                base_url=base_url,
                task_id=task_id,
            )

    @staticmethod
    def _is_search_no_invalid(response_dict):
        return 'list' not in response_dict

    @staticmethod
    def _extract_container_info_list(response_dict) -> List:
        container_data_list = response_dict.get('list')

        container_info_list = []
        for container_data in container_data_list:
            mbl_no = container_data['blNo'].strip()
            container_no = container_data['cntrNo'].strip()
            booking_no = container_data['bkgNo'].strip()
            cooperation_no = container_data['copNo'].strip()

            container_info_list.append(
                {
                    'mbl_no': mbl_no,
                    'container_no': container_no,
                    'booking_no': booking_no,
                    'cooperation_no': cooperation_no,
                }
            )

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
    def build_request_option(cls, booking_no, base_url, task_id) -> RequestOption:
        form_data = {
            'f_cmd': cls.f_cmd,
            'bkg_no': booking_no,
        }

        return RequestOption(
            method=RequestOption.METHOD_POST_FORM,
            rule_name=cls.name,
            url=base_url,
            form_data=form_data,
            meta={'task_id': task_id,}
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.json'

    def handle(self, response):
        task_id = response.meta['task_id']
        response_dict = json.loads(response.text)

        if self.__is_vessel_empty(response_dict=response_dict):
            yield VesselItem(task_id=task_id)
            return

        vessel_info_list = self._extract_vessel_info_list(response_dict=response_dict)
        for vessel_info in vessel_info_list:
            yield VesselItem(
                task_id=task_id,
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
    def __is_vessel_empty(response_dict) -> List:
        return 'list' not in response_dict

    @staticmethod
    def _extract_vessel_info_list(response_dict) -> List:
        vessel_data_list = response_dict['list']
        vessel_info_list = []
        for vessel_data in vessel_data_list:
            vessel_info_list.append(
                {
                    'name': vessel_data['vslEngNm'].strip(),
                    'voyage': vessel_data['skdVoyNo'].strip() + vessel_data['skdDirCd'].strip(),
                    'pol': vessel_data['polNm'].strip(),
                    'pod': vessel_data['podNm'].strip(),
                    'etd': vessel_data['etd'].strip() if vessel_data['etdFlag'] == 'C' else None,
                    'atd': vessel_data['etd'].strip() if vessel_data['etdFlag'] == 'A' else None,
                    'eta': vessel_data['eta'].strip() if vessel_data['etaFlag'] == 'C' else None,
                    'ata': vessel_data['eta'].strip() if vessel_data['etaFlag'] == 'A' else None,
                }
            )

        return vessel_info_list


class ContainerStatusRoutingRule(BaseRoutingRule):
    name = 'CONTAINER_STATUS'
    f_cmd = '125'

    @classmethod
    def build_request_option(cls, container_no, booking_no, cooperation_no, base_url, task_id) -> RequestOption:
        form_data = {
            'f_cmd': cls.f_cmd,
            'cntr_no': container_no,
            'bkg_no': booking_no,
            'cop_no': cooperation_no,
        }

        return RequestOption(
            method=RequestOption.METHOD_POST_FORM,
            rule_name=cls.name,
            url=base_url,
            form_data=form_data,
            meta={
                'container_key': container_no,
                'task_id': task_id,
            },
        )

    def get_save_name(self, response) -> str:
        container_key = response.meta['container_key']
        return f'{self.name}_{container_key}.json'

    def handle(self, response):
        task_id = response.meta['task_id']
        container_key = response.meta['container_key']
        response_dict = json.loads(response.text)

        container_status_list = self._extract_container_status_list(response_dict=response_dict)

        for container_status in container_status_list:
            yield ContainerStatusItem(
                task_id=task_id,
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

            container_status_info_list.append(
                {
                    'status': status,
                    'location': container_status_data['placeNm'].strip(),
                    'local_time': local_time,
                    'est_or_actual': container_status_data['actTpCd'].strip(),
                }
            )

        return container_status_info_list


class ReleaseStatusRoutingRule(BaseRoutingRule):
    name = 'RELEASE_STATUS'
    f_cmd = '126'

    @classmethod
    def build_request_option(cls, container_no, booking_no, base_url, task_id) -> RequestOption:
        form_data = {
            'f_cmd': cls.f_cmd,
            'cntr_no': container_no,
            'bkg_no': booking_no,
        }

        return RequestOption(
            method=RequestOption.METHOD_POST_FORM,
            rule_name=cls.name,
            url=base_url,
            form_data=form_data,
            meta={
                'container_key': container_no,
                'task_id': task_id,
            },
        )

    def get_save_name(self, response) -> str:
        container_key = response.meta['container_key']
        return f'{self.name}_{container_key}.json'

    def handle(self, response):
        task_id = response.meta['task_id']
        container_key = response.meta['container_key']
        response_dict = json.loads(response.text)

        release_info = self._extract_release_info(response_dict=response_dict)

        yield MblItem(
            task_id=task_id,
            freight_date=release_info['freight_date'] or None,
            us_customs_date=release_info['us_customs_date'] or None,
            us_filing_date=release_info['us_filing_date'] or None,
            firms_code=release_info['firms_code'] or None,
        )

        yield ContainerItem(
            task_id=task_id,
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
    def build_request_option(cls, container_no, cooperation, base_url,task_id) -> RequestOption:
        form_data = {
            'f_cmd': cls.f_cmd,
            'cop_no': cooperation,
        }

        return RequestOption(
            method=RequestOption.METHOD_POST_FORM,
            rule_name=cls.name,
            url=base_url,
            form_data=form_data,
            meta={
                'container_key': container_no,
                'task_id': task_id,
            },
        )

    def get_save_name(self, response) -> str:
        container_key = response.meta['container_key']
        return f'{self.name}_{container_key}.json'

    def handle(self, response):
        task_id = response.meta['task_id']
        container_key = response.meta['container_key']
        response_dict = json.loads(response.text)

        ready_for_pick_up = self._extract_ready_for_pick_up(response_dict=response_dict)

        yield ContainerItem(
            task_id=task_id,
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
