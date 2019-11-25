import scrapy
from scrapy import Selector

from crawler.core_carrier.base_spiders import BaseCarrierSpider
from crawler.core_carrier.rules import RuleManager, RoutingRequest, BaseRoutingRule
from crawler.core_carrier.items import (
    BaseCarrierItem, MblItem, LocationItem, VesselItem, ContainerItem, ContainerStatusItem)
from crawler.core_carrier.exceptions import CarrierResponseFormatError, CarrierInvalidMblNoError


class CarrierRclSpider(BaseCarrierSpider):
    name = 'carrier_rcl'

    def __init__(self, *args, **kwargs):
        super(CarrierRclSpider, self).__init__(*args, **kwargs)

        rules = [
            MainRoutingRule(),
            CargoTrackingRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)

    def start_requests(self):

        routing_request = MainRoutingRule.build_routing_request(mbl_no=self.mbl_no)
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


# -------------------------------------------------------------------------------

class MainRoutingRule(BaseRoutingRule):
    name = 'MAIN'

    @classmethod
    def build_routing_request(cls, mbl_no: str) -> RoutingRequest:
        request = scrapy.Request(
            url='https://www.rclgroup.com/Home',
            meta={'mbl_no': mbl_no},
        )
        return RoutingRequest(request=request, rule_name=cls.name)

    def handle(self, response):
        mbl_no = response.meta['mbl_no']

        hidden_div_list = response.css('div[class=aspNetHidden]')
        form_data = {}
        for div in hidden_div_list:
            for input in div.css('input'):
                name = input.css('::attr(name)').get()
                value = input.css('::attr(value)').get()
                form_data[name] = value
        captcha_value = response.css('input[name="ctl00$ContentPlaceHolder1$captchavalue"]::attr(value)').get()
        form_data['ctl00$ContentPlaceHolder1$cCaptcha'] = captcha_value
        form_data['ctl00$ContentPlaceHolder1$captchavalue'] = captcha_value
        yield CargoTrackingRoutingRule.build_routing_request(mbl_no=mbl_no, form_data=form_data)


# -------------------------------------------------------------------------------


class CargoTrackingRoutingRule(BaseRoutingRule):
    name = 'CARGO_TRACKING'

    @classmethod
    def build_routing_request(cls, mbl_no, form_data) -> RoutingRequest:
        form_data['ctl00$ContentPlaceHolder1$ctracking'] = mbl_no
        request = scrapy.FormRequest(
            url=f'https://www.rclgroup.com/923Cargo_Tracking231',
            formdata=form_data,
        )
        return RoutingRequest(request=request, rule_name=cls.name)

    def handle(self, response):
        yield MblItem()
