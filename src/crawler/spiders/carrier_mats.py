import json
import re
from typing import List, Dict

import scrapy

from crawler.core_carrier.base_spiders import BaseCarrierSpider
from crawler.core_carrier.exceptions import CarrierInvalidMblNoError
from crawler.core_carrier.items import BaseCarrierItem, MblItem, ContainerItem, ContainerStatusItem, LocationItem
from crawler.core_carrier.rules import RuleManager, RoutingRequest, BaseRoutingRule

URL = 'https://www.matson.com'


class CarrierMatsSpider(BaseCarrierSpider):
    name = 'carrier_mats'

    def __init__(self, *args, **kwargs):
        super(CarrierMatsSpider, self).__init__(*args, **kwargs)

        rules = [
            MainInfoRoutingRule(),
            TimeRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)

    def start_requests(self):
        routing_request = MainInfoRoutingRule.build_routing_request(mbl_no=self.mbl_no)
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


class MainInfoRoutingRule(BaseRoutingRule):
    name = 'MAIN_INFO'

    @classmethod
    def build_routing_request(cls, mbl_no: str) -> RoutingRequest:
        url = f'{URL}/vcsc/tracking/bill/{mbl_no}'
        request = scrapy.Request(url=url)
        return RoutingRequest(request=request, rule_name=cls.name)

    def handle(self, response):
        container_list = json.loads(response.text)
        self._check_mbl_no(container_list)

        unique_container_dict = self._extract_unique_container(container_list)

        for container_no, container in unique_container_dict.items():
            main_info = self._extract_main_info(container)
            yield MblItem(
                por=LocationItem(name=main_info['por_name']),
                pol=LocationItem(name=main_info['pol_name']),
                pod=LocationItem(name=main_info['pod_name']),
                final_dest=LocationItem(name=main_info['final_dest_name']),
            )

            yield ContainerItem(
                container_key=container_no,
                container_no=container_no,
            )

            container_status_list = self._extract_container_status_list(container)
            for status in container_status_list:
                status['container_key'] = container_no
                yield TimeRoutingRule.build_routing_request(status)

    @staticmethod
    def _check_mbl_no(container_list: List):
        if not container_list:
            raise CarrierInvalidMblNoError()

    @staticmethod
    def _extract_unique_container(container_list: List) -> Dict:
        unique_container_no_dict = {}
        for container in container_list:
            container_no = container['containerNumber'] + container['checkDigit']
            if container_no not in unique_container_no_dict:
                unique_container_no_dict[container_no] = container

        return unique_container_no_dict

    @staticmethod
    def _extract_main_info(container: Dict) -> Dict:
        return {
            'por_name': container['originPort'],
            'pol_name': container['loadPort'],
            'pod_name': container['dischargePort'],
            'final_dest_name': container['destPort'],
        }

    @staticmethod
    def _extract_container_status_list(container: Dict) -> List:
        status_list = container['events']
        multi_space_patt = re.compile(r'\s+')

        return_list = []
        for status in status_list:
            return_list.append({
                'timestamp': str(status['date']),
                'description': multi_space_patt.sub(' ', status['status']).strip(),
                'location_name': status['location'].strip() or None,
            })

        return return_list


class TimeRoutingRule(BaseRoutingRule):
    name = 'TIME'

    @classmethod
    def build_routing_request(cls, container_status: dict) -> RoutingRequest:
        url = f'{URL}/timezonerange.php'
        formdata = {'date': container_status['timestamp']}
        request = scrapy.FormRequest(url=url, formdata=formdata, meta={'status': container_status})
        return RoutingRequest(request=request, rule_name=cls.name)

    def handle(self, response):
        status = response.meta['status']
        local_date_time = response.text

        yield ContainerStatusItem(
            container_key=status['container_key'],
            local_date_time=local_date_time,
            location=LocationItem(name=status['location_name']),
            description=status['description'],
        )
