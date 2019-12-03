import json
import time
from typing import List, Dict, Union

import scrapy

from crawler.core_carrier.exceptions import CarrierInvalidMblNoError, CarrierResponseFormatError
from crawler.core_carrier.items import (
    LocationItem, MblItem, VesselItem, ContainerStatusItem, ContainerItem, BaseCarrierItem)
from crawler.core_carrier.base_spiders import BaseCarrierSpider
from crawler.core_carrier.rules import BaseRoutingRule, RoutingRequest, RuleManager
from crawler.utils.decorators import merge_yields


URL = 'http://elines.coscoshipping.com'
BASE = 'ebtracking/public'


class CarrierCosuSpider(BaseCarrierSpider):
    name = 'carrier_cosu'

    def __init__(self, *args, **kwargs):
        super(CarrierCosuSpider, self).__init__(*args, **kwargs)

        rules = [
            BillMainInfoRoutingRule(),
            BookingMainInfoRoutingRule(),
            BillContainerRoutingRule(),
            BookingContainerRoutingRule(),
            BillContainerStatusRoutingRule(),
            BookingContainerStatusRoutingRule(),
        ]

        self._rule_manager = RuleManager(rules=rules)

    def start_requests(self):
        routing_request = BillMainInfoRoutingRule.build_routing_request(mbl_no=self.mbl_no)
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


class BillMainInfoRoutingRule(BaseRoutingRule):
    name = 'BILL_MAIN_INFO'

    @classmethod
    def build_routing_request(cls, mbl_no: str) -> RoutingRequest:
        timestamp = build_timestamp()
        url = f'{URL}/{BASE}/bill/{mbl_no}?timestamp={timestamp}'
        request = scrapy.Request(url=url, meta={'mbl_no': mbl_no})
        return RoutingRequest(request=request, rule_name=cls.name)

    def handle(self, response):
        mbl_no = response.meta['mbl_no']

        response_dict = json.loads(response.text)
        message = response_dict['message']
        content = response_dict['data']['content']

        if message == '':
            for item in self._handle_bill_main_info(content=content):
                yield item
        else:
            # without bill
            booking_list = content['bookingNumbersInBillOfLadingTrackingGroupAssociationList']
            if booking_list:
                booking_no = booking_list[0]['trackingGroupReferenceCode']
                yield BookingMainInfoRoutingRule.build_routing_request(mbl_no=booking_no)
            else:
                yield BookingMainInfoRoutingRule.build_routing_request(mbl_no=mbl_no)

    def _handle_bill_main_info(self, content):
        tracking_info = self._extract_bill_tracking(content=content)
        ship_list = self._extract_actual_shipment(content=content)

        first_ship = ship_list[0]
        last_ship = ship_list[-1]
        mbl_no = tracking_info['mbl_no']

        yield MblItem(
            mbl_no=mbl_no,
            vessel=tracking_info['vessel'],
            voyage=tracking_info['voyage'],
            por=LocationItem(name=tracking_info['por_name']),
            pol=LocationItem(name=tracking_info['pol_name']),
            pod=LocationItem(
                name=tracking_info['pod_name'],
                firms_code=tracking_info['pod_firms_code'],
            ),
            final_dest=LocationItem(
                name=tracking_info['final_dest_name'],
                firms_code=tracking_info['final_dest_firms_code'],
            ),
            etd=first_ship['etd'],
            atd=first_ship['atd'],
            eta=last_ship['eta'],
            ata=last_ship['ata'],
            deliv_eta=tracking_info['pick_up_eta'],
            bl_type=tracking_info['bl_type'],
            cargo_cutoff_date=tracking_info['cargo_cutoff'],
            surrendered_status=tracking_info['bl_real_status'],
        )

        # Crawl information of vessel
        for ship in ship_list:
            vessel = ship['vessel']

            yield VesselItem(
                vessel_key=vessel,
                vessel=vessel,
                voyage=ship['voyage'],
                pol=LocationItem(name=ship['pol_name']),
                pod=LocationItem(name=ship['pod_name']),
                etd=ship['etd'],
                eta=ship['eta'],
                atd=ship['atd'],
                ata=ship['ata'],
                discharge_date=ship['discharge_date'],
                shipping_date=ship['shipping_date'],
                row_no=ship['row_no'],
                sequence_no=ship['seq_no'],
            )

        container_list = self._extract_container(content=content)
        for cargo in container_list:
            yield ContainerItem(
                container_key=cargo['container_key'],
                last_free_day=cargo['last_free_day'],
                empty_pickup_date=cargo['empty_pick_up'],
                empty_return_date=cargo['empty_return'],
                full_pickup_date=cargo['full_pick_up'],
                full_return_date=cargo['full_return'],
                ams_release=cargo['ams_release'],
                depot_last_free_day=cargo['depot_lfd'],
            )

        yield BillContainerRoutingRule.build_routing_request(mbl_no=mbl_no)

    @staticmethod
    def _extract_bill_tracking(content: Dict) -> Dict:
        tracking_path = strip_dict_value(dic=content['trackingPath'])
        tracking_na = strip_dict_value(dic=content['trackingNA'])

        pod_firms_code = None
        final_dest_firms_code = None

        if tracking_na:
            pod_firms_code = tracking_na['podFirmsCode']
            final_dest_firms_code = tracking_na['destinationFirmsCode']

        return {
            'mbl_no': tracking_path['billOfladingRefCode'],
            'vessel': tracking_path['vslNme'],
            'voyage': tracking_path['voyNumber'],
            'por_name': tracking_path['fromCity'],
            'pol_name': tracking_path['pol'],
            'pod_name': tracking_path['pod'],
            'final_dest_name': tracking_path['toCity'],
            'pick_up_eta': tracking_path['cgoAvailTm'],
            'bl_real_status': tracking_path['blRealStatus'],
            'bl_type': tracking_path['blType'],
            'pod_firms_code': pod_firms_code,
            'final_dest_firms_code': final_dest_firms_code,
            'cargo_cutoff': content['cargoCutOff']
        }

    @staticmethod
    def _extract_actual_shipment(content: Dict) -> List[Dict]:
        not_strip_actual_shipment_list = content['actualShipment']
        actual_shipment_list = []

        for not_strip_actual_shipment in not_strip_actual_shipment_list:
            actual_shipment = strip_dict_value(dic=not_strip_actual_shipment)
            actual_shipment_list.append(actual_shipment)
        actual_shipment_list = content['actualShipment']

        return_list = []

        for ship in actual_shipment_list:
            return_list.append({
                'vessel': ship['vesselName'],
                'voyage': ship['voyageNo'],
                'pol_name': ship['portOfLoading'],
                'pod_name': ship['portOfDischarge'],
                'etd': ship['expectedDateOfDeparture'],
                'eta': ship['estimatedDateOfArrival'],
                'atd': ship['actualDepartureDate'],
                'ata': ship['actualArrivalDate'],
                'row_no': ship['rownum'],
                'seq_no': ship['sequenceNumber'],
                'discharge_date': ship['actualDischargeDate'],
                'shipping_date': ship['actualShippingDate'],
            })
        return return_list

    @staticmethod
    def _extract_container(content: Dict) -> List:
        container_list = content['cargoTrackingContainer']

        return_list = []
        for cargo in container_list:
            container_no = cargo['cntrNum']
            container_key = get_container_key(container_no=container_no)

            return_list.append({
                'container_key': container_key,
                'empty_pick_up': cargo['emptyPickUpDt'],
                'full_return': cargo['ladenReturnDt'],
                'full_pick_up': cargo['ladenPickUpDt'],
                'empty_return': cargo['emptyReturnDt'],
                'last_free_day': cargo['lfd'],
                'ams_release': cargo['amsRelease'],
                'depot_lfd': cargo['depotLfd'],
            })

        return return_list


class BookingMainInfoRoutingRule(BaseRoutingRule):
    name = 'BOOKING_MAIN_INFO'

    @classmethod
    def build_routing_request(cls, mbl_no: str) -> RoutingRequest:
        timestamp = build_timestamp()
        url = f'{URL}/{BASE}/booking/{mbl_no}?timestamp={timestamp}'
        request = scrapy.Request(url=url)
        return RoutingRequest(request=request, rule_name=cls.name)

    def handle(self, response):
        response_dict = json.loads(response.text)
        content = response_dict['data']['content']
        self._check_mbl_no(response=response_dict)

        tracking_info = self._extract_booking_tracking(content=content)
        ship_list = self._extract_actual_shipment(content=content)

        first_ship = ship_list[0]
        last_ship = ship_list[-1]
        mbl_no = tracking_info['mbl_no']

        yield MblItem(
            mbl_no=mbl_no,
            vessel=tracking_info['vessel'],
            voyage=tracking_info['voyage'],
            por=LocationItem(name=tracking_info['por_name']),
            pol=LocationItem(name=tracking_info['pol_name']),
            pod=LocationItem(
                name=tracking_info['pod_name'],
                firms_code=tracking_info['pod_firms_code'],
            ),
            final_dest=LocationItem(
                name=tracking_info['final_dest_name'],
                firms_code=tracking_info['final_dest_firms_code'],
            ),
            etd=first_ship['etd'],
            atd=first_ship['atd'],
            eta=last_ship['eta'],
            ata=last_ship['ata'],
            deliv_eta=tracking_info['pick_up_eta'],
            cargo_cutoff_date=tracking_info['cargo_cutoff'],
            surrendered_status=tracking_info['bl_real_status'],
            trans_eta=tracking_info['trans_eta'],
            container_quantity=tracking_info['container_quantity'],
        )

        # Crawl information of vessel
        for ship in ship_list:
            vessel = ship['vessel']

            yield VesselItem(
                vessel_key=vessel,
                vessel=vessel,
                voyage=ship['voyage'],
                pol=LocationItem(name=ship['pol_name']),
                pod=LocationItem(name=ship['pod_name']),
                etd=ship['etd'],
                eta=ship['eta'],
                atd=ship['atd'],
                ata=ship['ata'],
                discharge_date=ship['discharge_date'],
                shipping_date=ship['shipping_date'],
                row_no=ship['row_no'],
                sequence_no=ship['seq_no'],
            )

        container_list = self._extract_container(content=content)
        for cargo in container_list:
            yield ContainerItem(
                container_key=cargo['container_key'],
                last_free_day=cargo['last_free_day'],
                empty_pickup_date=cargo['empty_pick_up'],
                empty_return_date=cargo['empty_return'],
                full_pickup_date=cargo['full_pick_up'],
                full_return_date=cargo['full_return'],
                ams_release=cargo['ams_release'],
                depot_last_free_day=cargo['depot_lfd'],
            )

        yield BookingContainerRoutingRule.build_routing_request(mbl_no=mbl_no)

    @staticmethod
    def _check_mbl_no(response: Dict):
        message = response['message']
        if message:
            raise CarrierInvalidMblNoError()

    @staticmethod
    def _extract_booking_tracking(content: Dict) -> Dict:
        tracking_path = strip_dict_value(dic=content['trackingPath'])
        tracking_na = strip_dict_value(dic=content['trackingNA'])
        pod_firms_code = None
        final_dest_firms_code = None

        if tracking_na:
            pod_firms_code = tracking_na['podFirmsCode']
            final_dest_firms_code = tracking_na['destinationFirmsCode']

        return {
            'mbl_no': tracking_path['trackingGroupReferenceCode'],
            'vessel': tracking_path['vslNme'],
            'voyage': tracking_path['voyNumber'],
            'por_name': tracking_path['fromCity'],
            'pol_name': tracking_path['pol'],
            'pod_name': tracking_path['pod'],
            'final_dest_name': tracking_path['toCity'],
            'pick_up_eta': tracking_path['cgoAvailTm'],
            'bl_real_status': content['blRealStatus'],
            'pod_firms_code': pod_firms_code,
            'final_dest_firms_code': final_dest_firms_code,
            'cargo_cutoff': content['cargoCutOff'],
            'container_quantity': tracking_path['containerQuantity'],
            'trans_eta': tracking_path['cgoFinalTm'],
        }

    @staticmethod
    def _extract_actual_shipment(content: Dict) -> List[Dict]:
        not_strip_actual_shipment_list = content['actualShipment']
        actual_shipment_list = []

        for not_strip_actual_shipment in not_strip_actual_shipment_list:
            actual_shipment = strip_dict_value(dic=not_strip_actual_shipment)
            actual_shipment_list.append(actual_shipment)
        actual_shipment_list = content['actualShipment']

        return_list = []

        for ship in actual_shipment_list:
            return_list.append({
                'vessel': ship['vesselName'],
                'voyage': ship['voyageNo'],
                'pol_name': ship['portOfLoading'],
                'pod_name': ship['portOfDischarge'],
                'etd': ship['expectedDateOfDeparture'],
                'eta': ship['estimatedDateOfArrival'],
                'atd': ship['actualDepartureDate'],
                'ata': ship['actualArrivalDate'],
                'row_no': ship['rownum'],
                'seq_no': ship['sequenceNumber'],
                'discharge_date': ship['actualDischargeDate'],
                'shipping_date': ship['actualShippingDate'],
            })
        return return_list

    @staticmethod
    def _extract_container(content: Dict) -> List:
        container_list = content['cargoTrackingContainer']

        return_list = []
        for cargo in container_list:
            container_no = cargo['cntrNum']
            container_key = get_container_key(container_no=container_no)

            return_list.append({
                'container_key': container_key,
                'empty_pick_up': cargo['emptyPickUpDt'],
                'full_return': cargo['ladenReturnDt'],
                'full_pick_up': cargo['ladenPickUpDt'],
                'empty_return': cargo['emptyReturnDt'],
                'last_free_day': cargo['lfd'],
                'ams_release': cargo['amsRelease'],
                'depot_lfd': cargo['depotLfd'],
            })

        return return_list


class BillContainerRoutingRule(BaseRoutingRule):
    name = 'BILL_CONTAINER'

    @classmethod
    def build_routing_request(cls, mbl_no: str) -> RoutingRequest:
        timestamp = build_timestamp()
        url = f'{URL}/{BASE}/bill/containers/{mbl_no}?timestamp={timestamp}'
        request = scrapy.Request(url=url, meta={'mbl_no': mbl_no})
        return RoutingRequest(request=request, rule_name=cls.name)

    def handle(self, response):
        mbl_no = response.meta['mbl_no']

        response_dict = json.loads(response.text)
        content = response_dict['data']['content']
        container_info = self._extract_container_info(content=content)

        for container in container_info:
            container_key = container['container_key']
            container_no = container['container_no']

            yield ContainerItem(
                container_key=container_key,
                container_no=container_no,
            )

            yield BillContainerStatusRoutingRule.build_routing_request(
                mbl_no=mbl_no, container_no=container_no, container_key=container_key)

    @staticmethod
    def _extract_container_info(content: Dict) -> List:
        container_list = []
        for container in content:
            container_no = container['containerNumber']
            container_key = get_container_key(container_no=container_no)

            container_list.append({
                'container_key': container_key,
                'container_no': container_no,
            })
        return container_list


class BookingContainerRoutingRule(BaseRoutingRule):
    name = 'BOOKING_CONTAINER'

    @classmethod
    def build_routing_request(cls, mbl_no: str) -> RoutingRequest:
        timestamp = build_timestamp()
        url = f'{URL}/{BASE}/booking/containers/{mbl_no}?timestamp={timestamp}'
        request = scrapy.Request(url=url, meta={'mbl_no': mbl_no})
        return RoutingRequest(request=request, rule_name=cls.name)

    def handle(self, response):
        mbl_no = response.meta['mbl_no']

        response_dict = json.loads(response.text)
        content = response_dict['data']['content']
        container_info = self._extract_container_info(content=content)

        for container in container_info:
            container_key = container['container_key']
            container_no = container['container_no']

            yield ContainerItem(
                container_key=container_key,
                container_no=container_no,
            )

            yield BookingContainerStatusRoutingRule.build_routing_request(
                mbl_no=mbl_no, container_no=container_no, container_key=container_key)

    @staticmethod
    def _extract_container_info(content: Dict) -> List:
        container_list = []
        for container in content:
            container_no = container['containerNumber']
            container_key = get_container_key(container_no=container_no)

            container_list.append({
                'container_key': container_key,
                'container_no': container_no,
            })
        return container_list


class BillContainerStatusRoutingRule(BaseRoutingRule):
    name = 'BILL_CONTAINER_STATUS'

    @classmethod
    def build_routing_request(cls, mbl_no: str, container_no: str, container_key: str) -> RoutingRequest:
        timestamp = build_timestamp()
        url = f'{URL}/{BASE}/container/status/{container_no}?billNumber={mbl_no}&timestamp={timestamp}'
        request = scrapy.Request(url=url, meta={'container_key': container_key})
        return RoutingRequest(request=request, rule_name=cls.name)

    def handle(self, response):
        container_key = response.meta['container_key']

        container_list = self._extract_container_status(response_str=response.text)

        for container in container_list:
            yield ContainerStatusItem(
                container_key=container_key,
                description=container['status'],
                local_date_time=container['local_date_time'],
                location=LocationItem(name=container['location']),
                transport=container['transport'],
            )

    @staticmethod
    def _extract_container_status(response_str: str) -> List:
        response_json = json.loads(response_str)
        not_strip_container_content = response_json['data']['content']
        container_content = []

        for not_strip_info in not_strip_container_content:
            info = strip_dict_value(dic=not_strip_info)
            container_content.append(info)

        return_list = []

        for info in container_content:
            return_list.append({
                'status': info['containerNumberStatus'],
                'transport': info['transportation'],
                'local_date_time': info['timeOfIssue'],
                'location': info['location']
            })
        return return_list


class BookingContainerStatusRoutingRule(BaseRoutingRule):
    name = 'BOOKING_CONTAINER_STATUS'

    @classmethod
    def build_routing_request(cls, mbl_no: str, container_no: str, container_key: str) -> RoutingRequest:
        timestamp = build_timestamp()
        url = f'{URL}/{BASE}/container/status/{container_no}?bookingNumber={mbl_no}&timestamp={timestamp}'
        request = scrapy.Request(url=url, meta={'container_key': container_key})
        return RoutingRequest(request=request, rule_name=cls.name)

    def handle(self, response):
        container_key = response.meta['container_key']

        container_list = self._extract_container_status(response_str=response.text)

        for container in container_list:
            yield ContainerStatusItem(
                container_key=container_key,
                description=container['status'],
                local_date_time=container['local_date_time'],
                location=LocationItem(name=container['location']),
                transport=container['transport'],
            )

    @staticmethod
    def _extract_container_status(response_str: str) -> List:
        response_json = json.loads(response_str)
        container_content = response_json['data']['content']
        return_list = []

        for info in container_content:
            return_list.append({
                'status': info['containerNumberStatus'],
                'transport': info['transportation'],
                'local_date_time': info['timeOfIssue'],
                'location': info['location']
            })
        return return_list


def build_timestamp():
    return int(time.time() * 1000)


def get_container_key(container_no: str):
    container_key = container_no[:10]

    if len(container_key) != 10:
        raise CarrierResponseFormatError(f'Invalid container_no `{container_no}`')

    return container_key


def strip_dict_value(dic: Union[Dict, None]) -> Union[Dict, None]:
    if dic is None:
        return dic

    striped_dict = {}
    for key, value in dic.items():
        value = value.strip() if isinstance(value, str) else value
        striped_dict[key] = value

    return striped_dict
