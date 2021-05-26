import json
import re
from datetime import datetime, timezone
from typing import List, Dict

import scrapy

from crawler.core_carrier.base_spiders import BaseCarrierSpider
from crawler.core_carrier.exceptions import (
    CarrierInvalidMblNoError,
    CarrierResponseFormatError,
    SuspiciousOperationError,
)
from crawler.core_carrier.items import (
    BaseCarrierItem,
    MblItem,
    ContainerItem,
    ContainerStatusItem,
    LocationItem,
    DebugItem,
)
from crawler.core_carrier.request_helpers import RequestOption
from crawler.core_carrier.rules import RuleManager, BaseRoutingRule


URL = 'https://www.mellship.com'
DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'


class CarrierMellSpider(BaseCarrierSpider):
    name = 'carrier_mell'

    def __init__(self, *args, **kwargs):
        super(CarrierMellSpider, self).__init__(*args, **kwargs)

        rules = [
            MainInfoRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)

    def start(self):
        request_option = MainInfoRoutingRule.build_request_option(mbl_no=self.mbl_no)
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
        meta = {RuleManager.META_CARRIER_CORE_RULE_NAME: option.rule_name, **option.meta}

        if option.method == RequestOption.METHOD_GET:
            return scrapy.Request(
                url=option.url,
                meta=meta,
            )
        else:
            raise SuspiciousOperationError(msg=f'Unexpected request method: `{option.method}`')


class MainInfoRoutingRule(BaseRoutingRule):
    name = 'MAIN_INFO'

    def __init__(self):
        self._patt_timestamp = re.compile(r'^/Date[(](?P<time>\d{10})\d{3}[)]/$')

    @classmethod
    def build_request_option(cls, mbl_no: str) -> RequestOption:
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=f'{URL}/Track/BL?blNo={mbl_no}',
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.json'

    def handle(self, response):
        response_dict = json.loads(response.text)

        self._check_mbl_no(response=response_dict)

        main_info = self._extract_main_info(response=response_dict)
        yield MblItem(
            pod=LocationItem(
                name=main_info['pod_name'],
                un_lo_code=main_info['pod_un_lo_code'],
            ),
            pol=LocationItem(
                name=main_info['pol_name'],
                un_lo_code=main_info['pol_un_lo_code'],
            ),
            eta=main_info['eta'],
            vessel=main_info['vessel'],
            voyage=main_info['voyage'],
        )

        container_list = response_dict['Containers']
        for container in container_list:
            container_info = self._extract_container_info(container=container)
            yield MblItem(
                mbl_no=container_info['mbl_no'],
            )

            container_no = container_info['container_no']
            yield ContainerItem(
                container_key=container_no,
                container_no=container_no,
            )

            container_status_list = self._extract_container_status(container=container)
            for container_status in container_status_list:
                yield ContainerStatusItem(
                    container_key=container_no,
                    local_date_time=container_status['local_date_time'],
                    location=LocationItem(name=container_status['location_name']),
                    description=container_status['description'],
                )

    @staticmethod
    def _check_mbl_no(response):
        if not response['FinalLeg']:
            raise CarrierInvalidMblNoError()

    def _extract_main_info(self, response: Dict) -> Dict:
        final_leg = response['FinalLeg']
        vessel_voyage = final_leg['LoadVoyage']
        voyage = vessel_voyage['VoyageCode'] + vessel_voyage['Bound']
        eta = self._timestamp_to_date(final_leg['ETA'])
        return {
            'pod_name': final_leg['DischargePortName'],
            'pod_un_lo_code': final_leg['DischargePortCode'],
            'eta': eta,
            'pol_name': final_leg['LoadPortName'],
            'pol_un_lo_code': final_leg['LoadPortCode'],
            'vessel': vessel_voyage['VesselName'],
            'voyage': voyage,
        }

    @staticmethod
    def _extract_container_info(container: Dict) -> Dict:
        return {
            'mbl_no': container['BLNo'],
            'container_no': container['ContainerNo'],
        }

    def _extract_container_status(self, container: Dict) -> List:
        container_status_list = container['Activities']

        return_container_status_list = []
        for container_status in container_status_list:
            local_date_time = self._timestamp_to_date(container_status['DateTime'])

            return_container_status_list.append(
                {
                    'local_date_time': local_date_time,
                    'location_name': f'{container_status["PortName"]} ({container_status["LocationName"]})',
                    'description': container_status['Name'],
                }
            )

        return return_container_status_list

    def _timestamp_to_date(self, timestamp: str) -> str:
        m = self._patt_timestamp.match(timestamp)

        if not m:
            CarrierResponseFormatError(reason=f'invalid timestamp: `{timestamp}`')

        t = int(m.group('time'))
        local_date_time = datetime.fromtimestamp(t, tz=timezone.utc)
        return local_date_time.strftime(DATETIME_FORMAT)
