import json
import re
from typing import List, Dict

import scrapy

from crawler.core_carrier.base_spiders import BaseMultiCarrierSpider
from crawler.core_carrier.exceptions import CarrierInvalidMblNoError, SuspiciousOperationError
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

URL = 'https://www.matson.com'


class CarrierMatsSpider(BaseMultiCarrierSpider):
    name = 'carrier_mats'

    def __init__(self, *args, **kwargs):
        super(CarrierMatsSpider, self).__init__(*args, **kwargs)

        rules = [
            MainInfoRoutingRule(),
            TimeRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)

    def start(self):
        for s_no, t_id in zip(self.search_nos, self.task_ids):
            request_option = MainInfoRoutingRule.build_request_option(mbl_no=s_no, task_id=t_id)
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
        elif option.method == RequestOption.METHOD_POST_FORM:
            return scrapy.FormRequest(
                url=option.url,
                formdata=option.form_data,
                meta=meta,
                dont_filter=True,
            )
        else:
            raise SuspiciousOperationError(msg=f'Unexpected request method: `{option.method}`')


class MainInfoRoutingRule(BaseRoutingRule):
    name = 'MAIN_INFO'

    @classmethod
    def build_request_option(cls, mbl_no: str, task_id: str) -> RequestOption:
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=f'{URL}/vcsc/tracking/bill/{mbl_no}',
            meta={'task_id': task_id,}
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.json'

    def handle(self, response):
        task_id = response.meta['task_id']
        container_list = json.loads(response.text)
        self._check_mbl_no(container_list)

        unique_container_dict = self._extract_unique_container(container_list)

        for container_no, container in unique_container_dict.items():
            main_info = self._extract_main_info(container)
            yield MblItem(
                task_id=task_id,
                por=LocationItem(name=main_info['por_name']),
                pol=LocationItem(name=main_info['pol_name']),
                pod=LocationItem(name=main_info['pod_name']),
                place_of_deliv=LocationItem(name=main_info['place_of_deliv_name']),
            )

            yield ContainerItem(
                task_id=task_id,
                container_key=container_no,
                container_no=container_no,
            )

            container_status_list = self._extract_container_status_list(container)
            for status in container_status_list:
                status['container_key'] = container_no
                yield TimeRoutingRule.build_request_option(task_id=task_id, container_status=status)

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
            'place_of_deliv_name': container['destPort'],
        }

    @staticmethod
    def _extract_container_status_list(container: Dict) -> List:
        status_list = container['events']
        multi_space_patt = re.compile(r'\s+')

        return_list = []
        for status in status_list:
            return_list.append(
                {
                    'timestamp': str(status['date']),
                    'description': multi_space_patt.sub(' ', status['status']).strip(),
                    'location_name': status['location'].strip() or None,
                }
            )

        return return_list


class TimeRoutingRule(BaseRoutingRule):
    name = 'TIME'

    @classmethod
    def build_request_option(cls, task_id: str, container_status: dict) -> RequestOption:
        form_data = {'date': container_status['timestamp']}

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_POST_FORM,
            url=f'{URL}/timezonerange.php',
            form_data=form_data,
            meta={
                'status': container_status,
                'task_id': task_id,
            },
        )

    def get_save_name(self, response) -> str:
        container_no = response.meta['status']['container_key']
        return f'{self.name}_{container_no}.json'

    def handle(self, response):
        task_id = response.meta['task_id']
        status = response.meta['status']
        local_date_time = response.text

        yield ContainerStatusItem(
            task_id=task_id,
            container_key=status['container_key'],
            local_date_time=local_date_time,
            location=LocationItem(name=status['location_name']),
            description=status['description'],
        )
