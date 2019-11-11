import json
import re
from datetime import datetime, timezone
from typing import List, Dict

import scrapy

from crawler.core_carrier.base_spiders import BaseCarrierSpider
from crawler.core_carrier.exceptions import CarrierInvalidMblNoError, CarrierResponseFormatError
from crawler.core_carrier.items import BaseCarrierItem, MblItem, ContainerItem, ContainerStatusItem, LocationItem
from crawler.core_carrier.rules import RuleManager, RoutingRequest, BaseRoutingRule
from crawler.utils.decorators import merge_yields


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

    def __init__(self):
        self._patt_timestamp = re.compile(r'^/Date[(](?P<time>\d{10})\d{3}[)]/$')

    @classmethod
    def build_routing_request(cls, mbl_no: str) -> RoutingRequest:
        url = f'{URL}/Track/BL?blNo={mbl_no}'
        request = scrapy.Request(url=url)
        return RoutingRequest(request=request, rule_name=cls.name)

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

            return_container_status_list.append({
                'local_date_time': local_date_time,
                'location_name': f'{container_status["PortName"]} ({container_status["LocationName"]})',
                'description': container_status['Name'],
            })

        return return_container_status_list

    def _timestamp_to_date(self, timestamp: str) -> str:
        m = self._patt_timestamp.match(timestamp)

        if not m:
            CarrierResponseFormatError(reason=f'invalid timestamp: `{timestamp}`')

        t = int(m.group('time'))
        local_date_time = datetime.fromtimestamp(t, tz=timezone.utc)
        return local_date_time.strftime(DATETIME_FORMAT)
