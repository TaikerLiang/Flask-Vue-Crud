# -*- coding: utf-8 -*-
import json
import time
from typing import List, Dict

import scrapy

from crawler.core_carrier.exceptions import CarrierInvalidMblNoError
from crawler.core_carrier.items import LocationItem, MblItem, VesselItem, ContainerStatusItem, ContainerItem
from crawler.core_carrier.spiders import CarrierSpiderBase
from crawler.utils import merge_yields


class UrlFactory:
    URL = 'http://elines.coscoshipping.com'
    BASE = 'ebtracking/public'

    def build_bill_url(self, mbl_no, follow_only=False):
        prefix = self._get_prefix(follow_only=follow_only)
        return f'{prefix}/{self.BASE}/bill/{mbl_no}?timestamp={self._timestamp}'

    def build_booking_url(self, mbl_no, follow_only=False):
        prefix = self._get_prefix(follow_only=follow_only)
        return f'{prefix}/{self.BASE}/booking/{mbl_no}?timestamp={self._timestamp}'

    def build_bill_containers_url(self, mbl_no, follow_only=False):
        prefix = self._get_prefix(follow_only=follow_only)
        return f'{prefix}/{self.BASE}/bill/containers/{mbl_no}?timestamp={self._timestamp}'

    def build_booking_containers_url(self, mbl_no, follow_only=False):
        prefix = self._get_prefix(follow_only=follow_only)
        return f'{prefix}/{self.BASE}/booking/containers/{mbl_no}?timestamp={self._timestamp}'

    def build_bill_container_status_url(self, mbl_no, container_no, follow_only=False):
        prefix = self._get_prefix(follow_only=follow_only)
        return f'{prefix}/{self.BASE}/container/status/{container_no}?billNumber={mbl_no}&timestamp={self._timestamp}'

    def build_booking_container_status_url(self, mbl_no, container_no, follow_only=False):
        prefix = self._get_prefix(follow_only=follow_only)
        return f'{prefix}/{self.BASE}/container/status/{container_no}?bookingNumber={mbl_no}&timestamp={self._timestamp}'

    def _get_prefix(self, follow_only: bool):
        return '' if follow_only else self.URL

    @property
    def _timestamp(self):
        return int(time.time() * 1000)


class CarrierCosuSpider(CarrierSpiderBase):
    name = 'carrier_cosu'

    urlFactory = UrlFactory()

    def start_requests(self):
        url = self.urlFactory.build_bill_url(mbl_no=self.mbl_no)
        yield scrapy.Request(url=url, callback=self.parse_main_info)

    @merge_yields
    def parse_main_info(self, response):
        response_dict = json.loads(response.text)
        message = response_dict['message']
        content = response_dict['data']['content']

        if message == '':
            for item in self.handle_bill_main_info(response=response, content=content):
                yield item
        else:
            # without bill
            if content['bookingNumbersInBillOfLadingTrackingGroupAssociationList']:
                url = self.urlFactory.build_booking_url(mbl_no=self.mbl_no)
                yield scrapy.Request(url=url, callback=self.parse_booking_main_info)
            else:
                raise CarrierInvalidMblNoError()

    def handle_bill_main_info(self, response, content):
        extractor = _MainInfoExtractor()

        tracking_info = extractor.extract_bill_tracking(content=content)
        ship_list = extractor.extract_actual_shipment(content=content)
        container_list = extractor.extract_container(content=content)

        first_ship = ship_list[0]
        last_ship = ship_list[-1]

        yield MblItem(
            mbl_no=tracking_info['mbl_no'],
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
            yield VesselItem(
                vessel=ship['vessel'],
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

        for cargo in container_list:
            yield ContainerItem(
                container_no=cargo['container_no'],
                last_free_day=cargo['last_free_day'],
                empty_pickup_date=cargo['empty_pick_up'],
                empty_return_date=cargo['empty_return'],
                full_pickup_date=cargo['full_pick_up'],
                full_return_date=cargo['full_return'],
                ams_release=cargo['ams_release'],
                depot_last_free_day=cargo['depot_lfd'],
            )
            container_no = cargo['container_no']
            url = self.urlFactory.build_bill_container_status_url(
                mbl_no=self.mbl_no, container_no=container_no, follow_only=True,
            )
            yield response.follow(url=url, callback=self.parse_container)
    
    @merge_yields
    def parse_booking_main_info(self, response):
        response_dict = json.loads(response.text)
        content = response_dict['data']['content']

        extractor = _MainInfoExtractor()

        tracking_info = extractor.extract_booking_tracking(content=content)
        ship_list = extractor.extract_actual_shipment(content=content)
        container_list = extractor.extract_container(content=content)

        first_ship = ship_list[0]
        last_ship = ship_list[-1]

        yield MblItem(
            mbl_no=tracking_info['mbl_no'],
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
            yield VesselItem(
                vessel=ship['vessel'],
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

        for cargo in container_list:
            yield ContainerItem(
                container_no=cargo['container_no'],
                last_free_day=cargo['last_free_day'],
                empty_pickup_date=cargo['empty_pick_up'],
                empty_return_date=cargo['empty_return'],
                full_pickup_date=cargo['full_pick_up'],
                full_return_date=cargo['full_return'],
                ams_release=cargo['ams_release'],
                depot_last_free_day=cargo['depot_lfd'],
            )
            container_no = cargo['container_no']
            url = self.urlFactory.build_booking_container_status_url(
                mbl_no=self.mbl_no, container_no=container_no, follow_only=True
            )
            yield response.follow(url=url, callback=self.parse_container)

    @merge_yields
    def parse_container(self, response):
        # test extract
        container_status_extractor = _ContainerStatusExtractor()
        container_list = container_status_extractor.extract_container_status(response_str=response.text)

        for container in container_list:
            yield ContainerStatusItem(
                container_no=container['container_no'],
                description=container['status'],
                timestamp=container['timestamp'],
                location=LocationItem(name=container['location']),
                transport=container['transport'],
            )


class _MainInfoExtractor:
    @staticmethod
    def extract_bill_tracking(content: Dict) -> Dict:
        tracking_path = content['trackingPath']
        tracking_na = content['trackingNA']
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
    def extract_booking_tracking(content: Dict) -> Dict:
        tracking_path = content['trackingPath']
        tracking_na = content['trackingNA']
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
    def extract_actual_shipment(content: Dict) -> List[Dict]:
        # Crawl information of vessel
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
    def extract_container(content: Dict) -> List:
        container_list = content['cargoTrackingContainer']
        return_list = []
        for cargo in container_list:
            return_list.append({
                'container_no': cargo['cntrNum'],
                'empty_pick_up': cargo['emptyPickUpDt'],
                'full_return': cargo['ladenReturnDt'],
                'full_pick_up': cargo['ladenPickUpDt'],
                'empty_return': cargo['emptyReturnDt'],
                'last_free_day': cargo['lfd'],
                'ams_release': cargo['amsRelease'],
                'depot_lfd': cargo['depotLfd'],
            })
        return return_list


class _ContainerStatusExtractor:
    @staticmethod
    def extract_container_status(response_str: str) -> List:
        response_json = json.loads(response_str)
        container_content = response_json['data']['content']
        return_list = []

        for info in container_content:
            return_list.append({
                'container_no': info['containerNumber'],
                'status': info['containerNumberStatus'],
                'transport': info['transportation'],
                'timestamp': info['timeOfIssue'],
                'location': info['location']
            })
        return return_list
