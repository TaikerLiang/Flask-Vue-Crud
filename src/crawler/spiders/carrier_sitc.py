import scrapy
from scrapy import Selector

from crawler.core_carrier.base_spiders import BaseCarrierSpider
from crawler.core_carrier.rules import RuleManager, RoutingRequest, BaseRoutingRule
from crawler.core_carrier.items import (
    BaseCarrierItem, MblItem, LocationItem, VesselItem, ContainerItem, ContainerStatusItem)
from crawler.core_carrier.exceptions import CarrierResponseFormatError, CarrierInvalidMblNoError

SITC_BASE_URL = 'http://www.sitcline.com/track/biz/trackCargoTrack.do'


class CarrierSitcSpider(BaseCarrierSpider):
    name = 'carrier_sitc'

    def __init__(self, *args, **kwargs):
        super(CarrierSitcSpider, self).__init__(*args, **kwargs)

        rules = [
            TrackRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)

    def start_requests(self):
        methods = ['billNoIndexBasicNew', 'billNoIndexSailingNew', 'billNoIndexContainersNew', 'boxNoIndex']
        for method in methods:
            basic_routing_request = TrackRoutingRule.build_routing_request(
                mbl_no=self.mbl_no,
                container_no=self.container_no,
                method=method,
            )
            yield self._rule_manager.build_request_by(routing_request=basic_routing_request)

    def parse(self, response):
        routing_rule = self._rule_manager.get_rule_by_response(response=response)

        for result in routing_rule.handle(response=response):
            if isinstance(result, BaseCarrierItem):
                yield result
            elif isinstance(result, RoutingRequest):
                yield self._rule_manager.build_request_by(routing_request=result)
            else:
                raise RuntimeError()


# -------------------------------------------------------------------------------


class TrackRoutingRule(BaseRoutingRule):
    name = 'TRACK'

    @classmethod
    def build_routing_request(cls, mbl_no: str, container_no: str, method) -> RoutingRequest:
        if method == 'boxNoIndex':
            request = scrapy.Request(
                url=f'{SITC_BASE_URL}?method={method}&containerNo={container_no}&blNo={mbl_no}',
                meta={'method': method},
            )
        else:
            form_data = {
                'blNo': mbl_no,
                'containerNo': container_no,
                'queryInfo': '{"queryObjectName": "com.sitc.track.bean.BlNoBkContainer4Track"}'
            }
            request = scrapy.FormRequest(
                url=f'{SITC_BASE_URL}?method={method}',
                formdata=form_data,
                meta={'method': method},
            )
        return RoutingRequest(request=request, rule_name=cls.name)

    def handle(self, response):
        method = response.meta['method']
        # with open(f'{method}.json', 'w') as f:
        #     f.write(response.text)

        # retrieve other containers
        if method == 'billNoIndexContainersNew':
            yield TrackRoutingRule.build_routing_request(
                mbl_no='SITDNBBK351734',
                container_no='SEGU7343124',
                method='boxNoIndex',
            )
        yield MblItem()