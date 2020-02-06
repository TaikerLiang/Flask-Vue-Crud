import json
import time
from typing import Dict

import scrapy

from crawler.core_carrier.base_spiders import BaseCarrierSpider
from crawler.core_carrier.exceptions import CarrierInvalidMblNoError
from crawler.core_carrier.items import BaseCarrierItem, MblItem, ContainerItem, ContainerStatusItem, LocationItem
from crawler.core_carrier.rules import RuleManager, RoutingRequest, BaseRoutingRule

URL = 'http://www.nbosco.com/sebusiness/ecm/ContainerMovement/selectCmContainerCurrent'


class Carrier12luSpider(BaseCarrierSpider):
    name = 'carrier_12lu'

    def __init__(self, *args, **kwargs):
        super(Carrier12luSpider, self).__init__(*args, **kwargs)

        rules = [
            ContainerStatusRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)

    def start_requests(self):
        routing_request = ContainerStatusRoutingRule.build_routing_request(mbl_no=self.mbl_no, page_no=1)
        yield self._rule_manager.build_request_by(routing_request=routing_request)

    def parse(self, response):
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


class ContainerStatusRoutingRule(BaseRoutingRule):
    name = 'CONTAINER_STATUS'

    @classmethod
    def build_routing_request(cls, mbl_no: str, page_no: int) -> RoutingRequest:
        timestamp = build_timestamp()
        request = scrapy.Request(
            url=f'{URL}?t={timestamp}&blNo={mbl_no}&pageNum={page_no}&pageSize=20',
            meta={'mbl_no': mbl_no, 'page_no': page_no},
        )
        return RoutingRequest(request=request, rule_name=cls.name)

    def get_save_name(self, response) -> str:
        mbl_no = response.meta['mbl_no']
        return f'{self.name}_{mbl_no}.json'

    def handle(self, response):
        page_no = response.meta['page_no']

        response_dict = json.loads(response.text)

        data = response_dict['data']
        self._check_mbl_no(data=data)
        records = response_dict['data']['records']

        mbl_no = self._extract_mbl_no(records=records)
        yield MblItem(mbl_no=mbl_no)

        container_status_list = self._extract_container_status_list(records=records)
        for container_status in container_status_list:
            container_no = container_status['container_no']

            yield ContainerItem(
                container_key=container_no,
                container_no=container_no,
            )

            yield ContainerStatusItem(
                container_key=container_no,
                description=container_status['description'],
                local_date_time=container_status['local_date_time'],
                location=LocationItem(name=container_status['location_name']),
                vessel=container_status['vessel'],
                voyage=container_status['voyage'],
            )

        total_page_no = data['totalPage']
        if page_no < total_page_no:
            yield self.build_routing_request(mbl_no=mbl_no, page_no=page_no + 1)

    @staticmethod
    def _check_mbl_no(data: Dict):
        if 'records' not in data:
            raise CarrierInvalidMblNoError()

    @staticmethod
    def _extract_mbl_no(records: Dict) -> str:
        mbl_no = records[0]['blNo']
        return mbl_no

    @staticmethod
    def _extract_container_status_list(records: Dict):
        container_status_list = []
        for record in records:
            container_status_list.append({
                'container_no': record['containerNo'],
                'description': record['movementCode'],
                'local_date_time': record['eventDate'],
                'location_name': record['eventPort'],
                'vessel': record['vesselCode'],
                'voyage': record['voyageNo'],
            })

        return container_status_list


def build_timestamp():
    return int(time.time() * 1000)
