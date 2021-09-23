import json
from typing import Dict

import scrapy
from urllib.parse import urlencode

from crawler.core_air.exceptions import AirInvalidMawbNoError
from crawler.core_air.base_spiders import BaseAirSpider
from crawler.core_air.request_helpers import RequestOption
from crawler.core_air.rules import RuleManager, BaseRoutingRule
from crawler.core_air.items import (
    BaseAirItem,
    AirItem,
    DebugItem,
)

URL = 'https://www.brcargo.com/NEC_WEB/Tracking/QuickTracking'
PREFIX = '695'


class AirEvaSpider(BaseAirSpider):
    name = 'air_eva'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        rules = [
            AirInfoRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)

    def start(self):
        request_option = AirInfoRoutingRule.build_request_option(mawb_no=self.mawb_no)
        yield self._build_request_by(option=request_option)

    def parse(self, response):
        yield DebugItem(info={'meta': dict(response.meta)})

        routing_rule = self._rule_manager.get_rule_by_response(response=response)
        save_name = routing_rule.get_save_name(response=response)
        self._saver.save(to=save_name, text=response.text)

        for result in routing_rule.handle(response=response):
            if isinstance(result, BaseAirItem):
                yield result
            elif isinstance(result, RequestOption):
                yield self._build_request_by(option=result)
            else:
                raise RuntimeError()

    def _build_request_by(self, option: RequestOption):
        meta = {
            RuleManager.META_AIR_CORE_RULE_NAME: option.rule_name,
            **option.meta,
        }

        if option.method == RequestOption.METHOD_POST_BODY:
            return scrapy.Request(
                method='POST',
                url=option.url,
                headers=option.headers,
                body=option.body,
                meta=meta,
                dont_filter=True,
            )
        else:
            raise ValueError(f"Invalid option.method [{option.method}]")


class AirInfoRoutingRule(BaseRoutingRule):
    name = 'AIR_INFO'

    @classmethod
    def build_request_option(cls, mawb_no: str) -> RequestOption:
        form_data = {
            'prefix': PREFIX,
            'AWBNo': mawb_no,
        }
        body = urlencode(query=form_data)
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_POST_BODY,
            url=f'{URL}/QuickTrackingGet',
            headers={
                'Connection': 'keep-alive',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'Referer': 'https://www.brcargo.com/NEC_WEB/Tracking/QuickTracking/Index',
                'Accept-Language': 'en-US,en;q=0.9',
            },
            body=body,
            meta={
                'mawb_no': mawb_no,
            }
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.json'

    def handle(self, response):
        response_dict = json.loads(response.text)
        if self.is_mawb_no_invalid(response_dict):
            raise AirInvalidMawbNoError()

        air_info = self._extract_air_info(response_dict)
        yield AirItem(**air_info)

    @staticmethod
    def is_mawb_no_invalid(response: Dict):
        if response['AWBNo'] is None:
            return True
        return False

    @staticmethod
    def _extract_air_info(response: Dict) -> Dict:
        atd = (
            f"{response['FlightInfoList'][0]['DepartureDate'].split()[0]} "
            f"{response['FlightInfoList'][0]['DepartureTime'].split()[0]}"
        )
        ata = (
            f"{response['FlightInfoList'][-1]['ArrivalDate'].split()[0]} "
            f"{response['FlightInfoList'][-1]['ArrivalTime'].split()[0]}"
        )
        return {
            'mawb': response['AWBNo'].split('-')[1],
            'origin': response['From'],
            'destination': response['To'],
            'pieces': response['TotalPieces'],
            'weight': response['TotalWeight'],
            'current_state': response['Status'],
            'atd': atd,
            'ata': ata,
        }

