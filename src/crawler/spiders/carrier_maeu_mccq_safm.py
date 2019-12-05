from typing import Dict, Tuple

import scrapy

import json

from crawler.core_carrier.base_spiders import BaseCarrierSpider
from crawler.core_carrier.rules import RuleManager, RoutingRequest, BaseRoutingRule
from crawler.core_carrier.items import (
    BaseCarrierItem, MblItem, LocationItem, ContainerItem, ContainerStatusItem)
from crawler.core_carrier.exceptions import CarrierInvalidMblNoError, CarrierResponseFormatError
from crawler.utils.decorators import merge_yields


class SharedSpider(BaseCarrierSpider):
    name = ''
    base_url_format = ''

    def __init__(self, *args, **kwargs):
        super(SharedSpider, self).__init__(*args, **kwargs)

        rules = [
            MainInfoRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)

    def start_requests(self):
        routing_request = MainInfoRoutingRule.build_routing_request(mbl_no=self.mbl_no, url_format=self.base_url_format)
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


class CarrierMaeuSpider(SharedSpider):
    name = 'carrier_maeu'
    base_url_format = 'https://api.maerskline.com/track/{mbl_no}'


class CarrierMccqSpider(SharedSpider):
    name = 'carrier_mccq'
    base_url_format = 'https://api.maerskline.com/track/{mbl_no}?operator=mcpu'


class CarrierSafmSpider(SharedSpider):
    name = 'carrier_safm'
    base_url_format = 'https://api.maerskline.com/track/{mbl_no}?operator=safm'


# -------------------------------------------------------------------------------


class MainInfoRoutingRule(BaseRoutingRule):
    name = 'MAIN_INFO'

    @classmethod
    def build_routing_request(cls, mbl_no: str, url_format: str) -> RoutingRequest:
        request = scrapy.Request(
            url=url_format.format(mbl_no=mbl_no),
        )
        return RoutingRequest(request=request, rule_name=cls.name)

    def handle(self, response):
        response_dict = json.loads(response.text)

        self.check_mbl_no(response_dict)

        mbl_no = self._extract_mbl_no(response_dict=response_dict)
        routing_info = self._extract_routing_info(response_dict=response_dict)

        yield MblItem(
            mbl_no=mbl_no,
            por=LocationItem(name=routing_info['por']),
            final_dest=LocationItem(name=routing_info['final_dest']),
        )

        containers = self._extract_containers(response_dict=response_dict)
        for container in containers:
            container_no = container['no']
            
            yield ContainerItem(
                container_key=container_no,
                container_no=container_no,
                final_dest_eta=container['final_dest_eta'],
            )

            for container_status in container['container_statuses']:
                yield ContainerStatusItem(
                    container_key=container_no,
                    description=container_status['description'],
                    local_date_time=container_status['timestamp'],
                    location=LocationItem(name=container_status['location_name']),
                    vessel=container_status['vessel'] or None,
                    voyage=container_status['voyage'] or None,
                    est_or_actual=container_status['est_or_actual'],
                )

    @staticmethod
    def check_mbl_no(response_dict):
        if 'error' in response_dict:
            raise CarrierInvalidMblNoError()

    @staticmethod
    def _extract_mbl_no(response_dict):
        return response_dict['tpdoc_num']

    def _extract_routing_info(self, response_dict):
        origin = response_dict['origin']
        destination = response_dict['destination']

        return {
            'por': self._format_location(loc_info=origin),
            'final_dest': self._format_location(loc_info=destination),
        }

    def _extract_containers(self, response_dict):
        containers = response_dict['containers']

        container_info_list = []
        for container in containers:
            container_statuses = []

            for location in container['locations']:
                location_name = self._format_location(loc_info=location)

                for event in location['events']:
                    timestamp, est_or_actual = self._get_time_and_status(event)

                    container_statuses.append({
                        'location_name': location_name,
                        'description': event['activity'],
                        'vessel': self._format_vessel_name(
                            vessel_name=event['vessel_name'], vessel_num=event['vessel_num']),
                        'voyage': event['voyage_num'],
                        'timestamp': timestamp,
                        'est_or_actual': est_or_actual,
                    })

            container_info_list.append({
                'no': container['container_num'],
                'final_dest_eta': container['eta_final_delivery'],
                'container_statuses': container_statuses,
            })

        return container_info_list

    @staticmethod
    def _format_location(loc_info: Dict):
        # terminal
        if loc_info['terminal']:
            terminal_str = f'{loc_info["terminal"]} -- '
        else:
            terminal_str = ''

        # state & country
        state_country_list = []

        if loc_info['state']:
            state_country_list.append(loc_info['state'])

        state_country_list.append(loc_info['country_code'])
        state_country_str = ', '.join(state_country_list)

        return f'{terminal_str}{loc_info["city"]} ({state_country_str})'

    @staticmethod
    def _format_vessel_name(vessel_name, vessel_num):
        name_list = []

        if vessel_name:
            name_list.append(vessel_name)

        if vessel_num:
            name_list.append(vessel_num)

        return ' '.join(name_list)

    @staticmethod
    def _get_time_and_status(event: Dict) -> Tuple:
        if 'actual_time' in event:
            return event['actual_time'], 'A'

        if 'expected_time' in event:
            return event['expected_time'], 'E'

        raise CarrierResponseFormatError(reason=f'Unknown time in container_status" `{event}`')
