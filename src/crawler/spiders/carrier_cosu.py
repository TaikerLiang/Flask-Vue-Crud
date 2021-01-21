import json
import time
import random
from typing import List, Dict, Union

import scrapy
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib3.exceptions import ReadTimeoutError

from crawler.core_carrier.exceptions import CarrierInvalidMblNoError, CarrierResponseFormatError, \
    SuspiciousOperationError, LoadWebsiteTimeOutFatal
from crawler.core_carrier.items import (
    LocationItem, MblItem, VesselItem, ContainerStatusItem, ContainerItem, BaseCarrierItem, DebugItem)
from crawler.core_carrier.base_spiders import BaseCarrierSpider
from crawler.core_carrier.request_helpers import RequestOption
from crawler.core_carrier.rules import BaseRoutingRule, RuleManager


URL = 'http://elines.coscoshipping.com'
BASE = 'ebtracking/public'


class CarrierCosuSpider(BaseCarrierSpider):
    name = 'carrier_cosu'

    def __init__(self, *args, **kwargs):
        super(CarrierCosuSpider, self).__init__(*args, **kwargs)

        rules = [
           MainInfoRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)

    def start(self):
        option = MainInfoRoutingRule.build_request_option(mbl_no=self.mbl_no)
        yield self.__build_request_by(option=option)

    def parse(self, response):
        yield DebugItem(info={'meta': dict(response.meta)})

        routing_rule = self._rule_manager.get_rule_by_response(response=response)

        save_name = routing_rule.get_save_name(response=response)
        self._saver.save(to=save_name, text=response.text)

        for result in routing_rule.handle(response=response):
            if isinstance(result, BaseCarrierItem):
                yield result
            elif isinstance(result, RequestOption):
                yield self.__build_request_by(option=result)
            else:
                raise RuntimeError()
            
    @staticmethod
    def __build_request_by(option: RequestOption):
        meta = {
            RuleManager.META_CARRIER_CORE_RULE_NAME: option.rule_name,
            **option.meta
        }

        if option.method == RequestOption.METHOD_GET:
            return scrapy.Request(
                method=option.method,
                headers=option.headers,
                url=option.url,
                meta=meta,
            )
        else:
            raise SuspiciousOperationError(msg=f'Unexpected request method: `{option.method}`')


class MainInfoRoutingRule(BaseRoutingRule):
    name = 'MAIN_INFO'

    @classmethod
    def build_request_option(cls, mbl_no) -> RequestOption:
        url = f'https://www.google.com'

        return RequestOption(
            method=RequestOption.METHOD_GET,
            rule_name=cls.name,
            url=url,
            meta={
                'mbl_no': mbl_no,
            },
        )

    def get_save_name(self, response) -> str:
        return f'{self.name}.html'


    def handle(self, response):
        mbl_no = response.meta['mbl_no']

        # self._check_mbl_no(response=response)

        content_getter = ContentGetter()
        response_text = content_getter.search_and_return(mbl_no=mbl_no)

        response_selector = scrapy.Selector(text=response_text)

        for item in self._handle_item(content_getter=content_getter, response=response_selector):
            yield item

    def _handle_item(self, content_getter, response: scrapy.Selector):
        mbl_data = self._extract_main_info(response=response)
        if 'mbl_no' not in mbl_data and 'booking_no' not in mbl_data:
            raise CarrierInvalidMblNoError()

        yield MblItem(
            mbl_no=mbl_data['mbl_no'] or mbl_data['booking_no'],
            vessel=mbl_data.get('vessel', None),
            voyage=mbl_data.get('voyage', None),
            por=LocationItem(name=mbl_data.get('por_name', None)),
            pol=LocationItem(name=mbl_data.get('pol_name', None)),
            pod=LocationItem(
                name=mbl_data.get('pod_name', None),
                firms_code=mbl_data.get('pod_firms_code', None),
            ),
            final_dest=LocationItem(
                name=mbl_data.get('final_dest_name', None),
                firms_code=mbl_data.get('final_dest_firms_code', None),
            ),
            etd=mbl_data.get('etd', None),
            atd=mbl_data.get('atd', None),
            eta=mbl_data.get('eta', None),
            ata=mbl_data.get('ata', None),
            deliv_eta=mbl_data.get('pick_up_eta', None),
            cargo_cutoff_date=mbl_data.get('cargo_cutoff', None),
            surrendered_status=mbl_data.get('surrendered_status', None),
            # trans_eta=data.get('trans_eta', None),
            # container_quantity=data.get('container_quantity', None),
        )

        vessel_data = self._extract_schedule_detail_info(response=response)
        for vessel in vessel_data:
            yield VesselItem(
                vessel_key=vessel['vessel'],
                vessel=vessel['vessel'],
                voyage=vessel['voyage'],
                pol=vessel['pol'],
                pod=vessel['pod'],
                etd=vessel['etd'],
                eta=vessel['eta'],
                atd=vessel['atd'],
                ata=vessel['ata'],
            )

        container_list, container_status_list = self._extract_container_status_info(content_getter=content_getter, response=response)

        for ct in container_list:
            yield ContainerItem(
                container_key=ct['container_key'],
                container_no=ct['container_no'],
                last_free_day=ct['last_free_day'],
                depot_last_free_day=ct['depot_last_free_day'],
            )

        for cts in container_status_list:
            yield ContainerStatusItem(
                container_key=cts['container_key'],
                description=cts['description'],
                local_date_time=cts['local_date_time'],
                location=cts['location'],
                transport=cts['transport'],
            )

    def _extract_main_info(self, response: scrapy.Selector) -> Dict:
        keys = response.xpath('//div[@class="ivu-col ivu-col-span-4 label"]/p/text()').extract()
        values = response.xpath('//div[@class="ivu-col ivu-col-span-8 content"]/p/text()').extract()
        data = {
            'mbl_no': '',
            'booking_no': '',
            'por_name': '',
            'final_dest_name': '',
            'pol_name': '',
            'pod_name': '',
            'vessel': '',
            'voyage': '',
            'pick_up_eta': '',
            'cargo_cutoff': '',
            'pod_firms_code': '',
            'final_dest_firms_code': '',
            'bl_type': '',
            'surrendered_status': '',
        }
        for idx in range(min(len(values), int(len(keys)/2))):
            if keys[2*idx].strip() == 'Bill of Lading Number' and not data['mbl_no']:
                data['mbl_no'] = values[idx].strip()
            elif keys[2*idx].strip() == 'Booking Number' and not data['booking_no']:
                data['booking_no'] = values[idx].strip()
            elif keys[2*idx].strip() == 'Place of Receipt' and not data['por_name']:
                data['por_name'] = values[idx].strip()
            elif keys[2*idx].strip() == 'Final Destination' and not data['final_dest_name']:
                data['final_dest_name'] = values[idx].strip()
            elif keys[2*idx].strip() == 'POL' and not data['pol_name']:
                data['pol_name'] = values[idx].strip()
            elif keys[2*idx].strip() == 'POD' and not data['pod_name']:
                data['pod_name'] = values[idx].strip()
            elif keys[2*idx].strip() == 'Vessel / Voyage' and not (data['vessel'] or data['voyage']):
                data['vessel'], data['voyage'] = values[idx].strip().split(' / ')
            elif keys[2*idx].strip() == 'ETA at Place of Delivery' and not data['pick_up_eta']:
                data['pick_up_eta'] = values[idx].strip()
            elif keys[2*idx].strip() == 'Cargo Cutoff' and not data['cargo_cutoff']:
                data['cargo_cutoff'] = values[idx].strip()
            elif keys[2*idx].strip() == 'POD Firms Code' and not data['pod_firms_code']:
                data['pod_firms_code'] = values[idx].strip()
            elif keys[2*idx].strip() == 'Final Destination Firms Code' and not data['final_dest_firms_code']:
                data['final_dest_firms_code'] = values[idx].strip()
            elif keys[2*idx].strip() == 'B/L Type' and not data['bl_type']:
                data['bl_type'] = values[idx].strip()
            elif keys[2*idx].strip() == 'BL Surrendered Status' and not data['surrendered_status']:
                data['surrendered_status'] = values[idx].strip()

        departure_key = response.xpath('/html/body/div[1]/div[4]/div[1]/div/div[2]/div/div/div[2]/div[1]/div[2]/div/div[2]/div[3]/div[2]/div/div[2]/text()').get()
        departure_value = response.xpath('/html/body/div[1]/div[4]/div[1]/div/div[2]/div/div/div[2]/div[1]/div[2]/div/div[2]/div[3]/div[2]/div/div[3]/text()').get()
        if departure_key == "ATD":
            data['atd'] = departure_value
            data['etd'] = None
        else:
            data['atd'] = None
            data['etd'] = departure_value

        arrival_key = response.xpath('/html/body/div[1]/div[4]/div[1]/div/div[2]/div/div/div[2]/div[1]/div[2]/div/div[4]/div[3]/div[2]/div/div[2]/text()').get()
        arrival_value = response.xpath('/html/body/div[1]/div[4]/div[1]/div/div[2]/div/div/div[2]/div[1]/div[2]/div/div[4]/div[3]/div[2]/div/div[3]/text()').get()
        if arrival_key == "ATA":
            data['ata'] = arrival_value
            data['eta'] = None
        elif arrival_key == "ETA":
            data['ata'] = None
            data['eta'] = arrival_value

        arrival_key = response.xpath('/html/body/div[1]/div[4]/div[1]/div/div[2]/div/div/div[2]/div[1]/div[2]/div/div[3]/div[3]/div[2]/div/div[2]/text()').get()
        arrival_value = response.xpath('/html/body/div[1]/div[4]/div[1]/div/div[2]/div/div/div[2]/div[1]/div[2]/div/div[3]/div[3]/div[2]/div/div[3]/text()').get()
        if arrival_key == "ATA":
            data['ata'] = arrival_value
            data['eta'] = None
        elif arrival_key == "ETA":
            data['ata'] = None
            data['eta'] = arrival_value

        return data

    def _extract_schedule_detail_info(self, response: scrapy.Selector) -> List:
        BASE = '/html/body/div[1]/div[4]/div[1]/div/div[2]/div/div/div[2]/div[1]/div[3]/div/div/div[2]/table'
        tr_list = response.xpath(f'{BASE}/tbody/tr')
        data = []
        for idx in range(len(tr_list)):
            vessel = response.xpath(f'{BASE}/tbody/tr[{idx+1}]/td[1]/div/a/text()').get()
            voyage = response.xpath(f'{BASE}/tbody/tr[{idx+1}]/td[2]/div/div/p[2]/span[2]/text()').get()

            pol_name = response.xpath(f'{BASE}/tbody/tr[{idx+1}]/td[3]/div/span/text()').get()
            pod_name = response.xpath(f'{BASE}/tbody/tr[{idx+1}]/td[6]/div/span/text()').get()
            etd = response.xpath(f'{BASE}/tbody/tr[{idx+1}]/td[5]/div/div/p[1]/span[2]/text()').get()
            atd = response.xpath(f'{BASE}/tbody/tr[{idx+1}]/td[5]/div/div/p[2]/span[2]/text()').get()
            eta = response.xpath(f'{BASE}/tbody/tr[{idx+1}]/td[7]/div/div/p[1]/span[2]/text()').get()
            ata = response.xpath(f'{BASE}/tbody/tr[{idx+1}]/td[7]/div/div/p[2]/span[2]/text()').get()

            data.append({
                'vessel_key': vessel,
                'vessel': vessel,
                'voyage': voyage,
                'pol': LocationItem(name=pol_name),
                'pod': LocationItem(name=pod_name),
                'etd': etd,
                'eta': eta,
                'atd': atd,
                'ata': ata,
            })

        return data

    def _extract_container_status_info(self, content_getter, response: scrapy.Selector):
        CONTAINER_BASE = '/html/body/div[1]/div[4]/div[1]/div/div[2]/div/div/div[2]/div[1]/div[5]/div/div/div[2]/table'
        container_tr_list = response.xpath(f'{CONTAINER_BASE}/tbody/tr')

        content_getter.scroll_to_bottom_of_page()
        container_list = []
        container_status_list = []
        for ct_idx in range(len(container_tr_list)):

            container_no = response.xpath(f'{CONTAINER_BASE}/tbody/tr[{ct_idx+1}]/td[1]/div/div[1]/p[1]/span/text()').get()
            last_free_day, depot_lfd = None, None
            key_last_free_day = response.xpath(f'{CONTAINER_BASE}/tbody/tr[{ct_idx+1}]/td[3]/div/div/p[1]/span[1]/text()').get()
            key_depot_lfd = response.xpath(f'{CONTAINER_BASE}/tbody/tr[{ct_idx+1}]/td[3]/div/div/p[2]/span[1]/text()').get()

            if key_last_free_day and key_last_free_day.strip() == 'LFD:':
                last_free_day = response.xpath(f'{CONTAINER_BASE}/tbody/tr[1]/td[3]/div/div/p[1]/span[2]/text()').get()
                if last_free_day:
                    last_free_day = last_free_day.strip()

            if key_depot_lfd and key_depot_lfd.strip() == 'Depot LFD:':
                depot_lfd = response.xpath(f'{CONTAINER_BASE}/tbody/tr[1]/td[3]/div/div/p[2]/span[2]/text()').get()
                if last_free_day:
                    last_free_day = last_free_day.strip()

            container_list.append(
                {
                    'container_key': get_container_key(container_no=container_no),
                    'container_no': container_no,
                    'last_free_day': last_free_day,
                    'depot_last_free_day': depot_lfd,
                }
            )

            response = content_getter.click_container_status_button(ct_idx+1)
            response = scrapy.Selector(text=response)
            CONTAINER_STATUS_BASE = f'{CONTAINER_BASE}/tbody/tr[{ct_idx+1}]/td[1]/div/div[2]/div/div[2]/div/div[2]/div[2]/div/div/div/div/div/div/div[2]/table'
            container_status_tr_list = response.xpath(f'{CONTAINER_STATUS_BASE}/tbody/tr')

            for cts_idx in range(len(container_status_tr_list)):
                description = response.xpath(f'{CONTAINER_STATUS_BASE}/tbody/tr[{cts_idx+1}]/td[2]/div/div/p[1]/span/text()').get()
                local_date_time = response.xpath(f'{CONTAINER_STATUS_BASE}/tbody/tr[{cts_idx+1}]/td[2]/div/div/p[2]/span/text()').get()
                transport = response.xpath(f'{CONTAINER_STATUS_BASE}/tbody/tr[{cts_idx+1}]/td[2]/div/div/p[3]/span[2]/text()').get()
                location = response.xpath(f'{CONTAINER_STATUS_BASE}/tbody/tr[{cts_idx+1}]/td[3]/div/span/text()').get()

                container_status_list.append(
                    {
                        'container_key': get_container_key(container_no=container_no),
                        'description': description,
                        'local_date_time': local_date_time,
                        'transport': transport,
                        'location': LocationItem(name=location),
                    }
                )

        return container_list, container_status_list


class ContentGetter:
    def __init__(self):
        options = webdriver.FirefoxOptions()
        options.add_argument('--headless')
        options.add_argument(
            f'user-agent={self._random_choose_user_agent()}'
        )
        self._driver = webdriver.Firefox(firefox_options=options)

    def search_and_return(self, mbl_no: str):
        self._driver.get('https://elines.coscoshipping.com/ebusiness/cargoTracking')
        
        # cookie
        try:
            accept_btn = WebDriverWait(self._driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "/html/body/div[3]/div[2]/div/div/div[3]/div/button"))
            )
        except (TimeoutException, ReadTimeoutError):
            raise LoadWebsiteTimeOutFatal()

        # accept cookie
        time.sleep(1)
        accept_btn.click()
        time.sleep(1)

        self._driver.get(f'https://elines.coscoshipping.com/ebusiness/cargoTracking?trackingType=BOOKING&number={mbl_no}')

        try:
            time.sleep(10)
            return self._driver.execute_script("return document.getElementsByTagName('html')[0].innerHTML")
        except TimeoutException:
            raise LoadWebsiteTimeOutFatal()

    def click_container_status_button(self, idx: int):
        button = self._driver.find_element_by_xpath(
            f"/html/body/div[1]/div[4]/div[1]/div/div[2]/div/div/div[2]/div[1]/div[5]/div/div/div[2]/table/tbody/tr[{idx}]/td[1]/div/div[2]/div/div[1]/div/i"
        )
        button.click()
        time.sleep(8)
        return self._driver.execute_script("return document.getElementsByTagName('html')[0].innerHTML")

    def scroll_to_bottom_of_page(self):
        self._driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)

    @staticmethod
    def _random_choose_user_agent():
        user_agents = [
            # firefox
            (
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:80.0) '
                'Gecko/20100101 '
                'Firefox/80.0'
            ),
            (
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:79.0) '
                'Gecko/20100101 '
                'Firefox/79.0'
            ),
            (
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:78.0) '
                'Gecko/20100101 '
                'Firefox/78.0'
            ),
            (
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:78.0.1) '
                'Gecko/20100101 '
                'Firefox/78.0.1'
            ),
        ]

        return random.choice(user_agents)


def get_container_key(container_no: str):
    container_key = container_no[:10]

    if len(container_key) != 10:
        raise CarrierResponseFormatError(f'Invalid container_no `{container_no}`')

    return container_key
