import datetime
import json
from typing import Dict, List

import scrapy

from crawler.core_vessel.items import DebugItem
from crawler.core_vessel.request_helpers import RequestOption
from crawler.core_vessel.rules import BaseRoutingRule, RuleManager
from crawler.core_vessel.base_spiders import BaseVesselSpider
from crawler.core_vessel.items import VesselPortItem, BaseVesselItem
from crawler.utils.selenium import BaseChromeDriver

BASE_URL = 'https://www.bigschedules.com'

EMAIL_ADDRESS = 'cherubwang110@gmail.com'
PASSWORD = 'Crawler888'


class VesselBigSchedulesSpider(BaseVesselSpider):
    name = 'vessel_big_schedules'

    def __init__(self, *args, **kwargs):
        super(VesselBigSchedulesSpider, self).__init__(*args, **kwargs)

        rules = [
            LoginRoutingRule(),
            CarrierIDRoutingRule(),
            VesselGidRoutingRule(),
            VesselScheduleRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)

    def start(self):
        request_option = LoginRoutingRule.build_request_option(scac=self.scac, vessel_name=self.vessel_name)
        yield self._build_request_by(option=request_option)

    def parse(self, response):
        yield DebugItem(info={'meta': dict(response.meta)})

        routing_rule = self._rule_manager.get_rule_by_response(response=response)

        save_name = routing_rule.get_save_name(response=response)
        self._saver.save(to=save_name, text=response.text)

        for result in routing_rule.handle(response=response):
            if isinstance(result, BaseVesselItem):
                yield result
            elif isinstance(result, RequestOption):
                yield self._build_request_by(option=result)
            else:
                raise RuntimeError()

    def _build_request_by(self, option: RequestOption):
        meta = {
            RuleManager.META_VESSEL_CORE_RULE_NAME: option.rule_name,
            **option.meta,
        }

        if option.method == RequestOption.METHOD_POST_BODY:
            return scrapy.Request(
                method='POST',
                url=option.url,
                headers=option.headers,
                body=option.body,
                meta=meta,
            )
        elif option.method == RequestOption.METHOD_GET:
            return scrapy.Request(
                url=option.url,
                headers=option.headers,
                cookies=option.cookies,
                meta=meta,
            )
        else:
            raise RuntimeError()


class LoginRoutingRule(BaseRoutingRule):
    name = 'LOGIN'

    @classmethod
    def build_request_option(cls, scac, vessel_name) -> RequestOption:
        url = f'{BASE_URL}/api/admin/login'

        login_data = {
            "emailAddress": EMAIL_ADDRESS,
            "password": PASSWORD,
            "DISABLE_ART": "true",
        }

        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_POST_BODY,
            url=url,
            body=json.dumps(login_data),
            headers={
                'Accept': 'application/json, text/plain, */*',
                'Sec-Fetch-Dest': 'empty',
                'Content-Type': 'application/json;charset=UTF-8'
            },
            meta={
                'scac': scac,
                'vessel_name': vessel_name,
            },
        )

    def handle(self, response):
        scac = response.meta['scac']
        vessel_name = response.meta['vessel_name']

        cookies = {}
        for cookie in response.headers.getlist('Set-Cookie'):
            item = cookie.decode('utf-8').split(';')[0]
            key, value = item.split('=')
            cookies[key] = value

        yield CarrierIDRoutingRule.build_request_option(scac=scac, vessel_name=vessel_name, cookies=cookies)

    def get_save_name(self, response) -> str:
        return f'{self.name}.html'


class CarrierIDRoutingRule(BaseRoutingRule):
    name = 'CARRIER_ID'

    @classmethod
    def build_request_option(cls, scac, vessel_name, cookies) -> RequestOption:
        url = f'{BASE_URL}/api/carrier/fuzzyQuery'
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=url,
            cookies=cookies,
            meta={
                'scac': scac,
                'vessel_name': vessel_name,
            },
        )

    def handle(self, response):
        scac = response.meta['scac']
        vessel_name = response.meta['vessel_name']

        carrier_id_list = json.loads(response.text)
        carrier_id = self.__extract_carrier_id(carrier_id_list=carrier_id_list, scac=scac)

        yield VesselGidRoutingRule.build_request_option(scac=scac, vessel_name=vessel_name, carrier_id=carrier_id)

    def get_save_name(self, response) -> str:
        return f'{self.name}.html'

    @staticmethod
    def __extract_carrier_id(carrier_id_list: List, scac: str) -> str:
        for carrier in carrier_id_list:
            if carrier['scac'] == scac:
                return carrier['carrierID']

        raise RuntimeError()


class VesselGidRoutingRule(BaseRoutingRule):
    name = 'VESSEL_GID'

    @classmethod
    def build_request_option(cls, scac, vessel_name, carrier_id) -> RequestOption:
        url = f'{BASE_URL}/api/vessel/list?carrierId={carrier_id}&vesselName={vessel_name}'
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=url,
            meta={
                'scac': scac,
                'vessel_name': vessel_name,
                'carrier_id': carrier_id,
            }
        )

    def handle(self, response):
        scac = response.meta['scac']
        vessel_name = response.meta['vessel_name']
        carrier_id = response.meta['carrier_id']

        vessel_gid_list = json.loads(response.text)
        vessel_gid = self.__extract_vessel_gid(vessel_gid_list=vessel_gid_list, vessel_name=vessel_name)

        # click search button to get user detect cookie
        big_schedule_chrome_driver = BigSchedulesChromeDriver()
        cookie = big_schedule_chrome_driver.get_user_detect_cookie()

        yield VesselScheduleRoutingRule.build_request_option(
            cookie=cookie,
            carrier_id=carrier_id,
            scac=scac,
            vessel_gid=vessel_gid,
            vessel_name=vessel_name,
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.html'

    @staticmethod
    def __extract_vessel_gid(vessel_gid_list: List, vessel_name: str) -> str:
        vessel_info = vessel_gid_list[0]

        if vessel_info['name'] == vessel_name:
            return vessel_info['vesselGid']

        raise RuntimeError()


class VesselScheduleRoutingRule(BaseRoutingRule):
    name = 'VESSEL_SCHEDULE'

    @classmethod
    def build_request_option(cls, cookie, carrier_id, scac, vessel_gid, vessel_name) -> RequestOption:
        local_date_time = cls.__get_local_date_time()
        url = f'{BASE_URL}/api/vesselSchedule/list?_={local_date_time}&carrierId={carrier_id}&scac={scac}&vesselGid={vessel_gid}&vesselName={vessel_name}'
        return RequestOption(
            rule_name=cls.name,
            method=RequestOption.METHOD_GET,
            url=url,
            cookies=cookie,
            headers={
                'accept': "application/json, text/plain, */*",
                'sec-fetch-dest': "empty",
            },
        )

    def handle(self, response):
        response_dict = json.loads(response.text)

        port_info_list = self.__extract_port_info_list(response=response_dict)

        for port_info in port_info_list:
            yield VesselPortItem(
                etd=port_info['etd'],
                atd=port_info['atd'],
                eta=port_info['eta'],
                ata=port_info['ata'],
                name=port_info['name'],
                un_lo_code=port_info['un_lo_code'],
            )

    def get_save_name(self, response) -> str:
        return f'{self.name}.html'

    @staticmethod
    def __extract_port_info_list(response: Dict) -> List:
        ports_list = response['ports']

        return_list = []
        for port in ports_list:
            departure = port['departure']
            arrival = port['arrival']

            return_list.append({
                'etd': departure['estimated'],
                'atd': departure.get('actual'),
                'eta': arrival['estimated'],
                'ata': arrival.get('actual'),
                'name': port['name'],
                'un_lo_code': port['unlocode'],
            })

        return return_list

    @staticmethod
    def __get_local_date_time() -> str:
        return datetime.datetime.now().strftime('%Y%m%d%H')


class BigSchedulesChromeDriver(BaseChromeDriver):

    def __init__(self):
        extra_chrome_options = ["--window-size=1920,1080"]
        super().__init__(extra_chrome_options=extra_chrome_options)

    def get_user_detect_cookie(self):
        self._browser.get(BASE_URL)

        # close allow cookies popup
        allow_cookies_usage_button_xpath = "//button[@class='csck-btn csck-btn-solid']"
        self._click_button(xpath=allow_cookies_usage_button_xpath, wait_time=5)

        # close ad popup
        close_ad_button_xpath = "//span[@id='main_feature_beta_span_close']"
        self._click_button(xpath=close_ad_button_xpath, wait_time=10)

        # click search button
        search_button_xpath = "//a[@id='main_a_search']"
        self._click_button(xpath=search_button_xpath, wait_time=15)

        user_detect_cookie = {}

        for cookie in self._browser.get_cookies():
            if cookie['name'] == 'USER_BEHAVIOR_DETECT':
                user_detect_cookie[cookie['name']] = cookie['value']
                break

        return user_detect_cookie
