import dataclasses

import scrapy
from scrapy import Selector

import src.crawler.core_carrier.spiders as spider
from crawler.core_carrier.exceptions import CarrierInvalidMblNoError, CarrierResponseFormatError
from crawler.core_carrier.items import MblItem, LocationItem, VesselItem, ContainerItem, ContainerStatusItem
from crawler.extractors.table_cell_extractors import BaseTableCellExtractor, FirstTextTdExtractor
from crawler.extractors.table_extractors import (
    TableExtractor, TopHeaderTableLocator, TopLeftHeaderTableLocator, LeftHeaderTableLocator)
from crawler.utils import merge_yields


class UrlFactory:
    BASE_URL = 'https://www.hmm21.com/ebiz/track_trace'

    def build_homepage_url(self):
        return f'{self.BASE_URL}/main_new.jsp?null'

    def build_mbl_url(self):
        return f'{self.BASE_URL}/trackCTP_nTmp.jsp'

    def build_container_url(self, mbl_no):
        return f'{self.BASE_URL}/trackCTP_nTmp.jsp?US_IMPORT=Y&BNO_IMPORT={mbl_no}'

    def build_availability_url(self):
        return f'{self.BASE_URL}/WUTInfo.jsp'


class FormDataFactory:
    @staticmethod
    def _build_numbers_list(mbl_no):
        return [
            mbl_no,
            '', '', '', '', '',
            '', '', '', '', '',
            '', '', '', '', '',
            '', '', '', '', '',
            '', '', '',
        ]

    def build_main_info_formdata(self, mbl_no):
        return {
            'number': mbl_no,
            'type': '1',
            'selectedContainerIndex': '',
            'blFields': '3',
            'cnFields': '3',
            'is_quick': 'Y',
            'numbers': self._build_numbers_list(mbl_no),
        }

    def build_container_formdata(self, mbl_no, container_index, h_num):
        return {
            'selectedContainerIndex': f'{container_index}',
            'hNum': f'{h_num}',
            'tempBLOrBKG': mbl_no,
            'numbers': self._build_numbers_list(mbl_no),
        }

    @staticmethod
    def build_availability_formdata(mbl_no, container_no):
        return {
            'bno': mbl_no,
            'cntrNo': f'{container_no}',
        }


class CarrierHdmuSpider(spider.CarrierSpiderBase):
    name = 'carrier_hdmu'
    headers = {
        'Upgrade-Insecure-Requests': '1',
    }
    
    def __init__(self, *args, **kwargs):
        super(CarrierHdmuSpider, self).__init__(*args, **kwargs)
        self.url_factory = UrlFactory()
        self.formdata_factory = FormDataFactory()

    def start_requests(self):
        url = self.url_factory.build_homepage_url()

        yield scrapy.Request(
            url=url,
            headers=self.headers,
            callback=self.parse_home_page,
        )

    def parse(self, response):
        raise RuntimeError()

    # for cookies purpose
    def parse_home_page(self, response):
        formdata = self.formdata_factory.build_main_info_formdata(mbl_no=self.mbl_no)
        url = self.url_factory.build_mbl_url()

        yield scrapy.FormRequest(
            url=url,
            headers=self.headers,
            formdata=formdata,
            callback=self.parse_main_info,
        )

    @merge_yields
    def parse_main_info(self, response):
        err_message = _Extractor.extract_error_message(response=response)
        if err_message == 'B/L number is invalid.  Please try it again with correct number.':
            raise CarrierInvalidMblNoError()
        
        tracking_results = _Extractor.extract_tracking_results(response=response)
        customs_status = _Extractor.extract_customs_status(response=response)
        cargo_delivery_info = _Extractor.extract_cargo_delivery_info(response=response)
        latest_update = _Extractor.extract_lastest_update(response=response)

        yield MblItem(
            mbl_no=self.mbl_no,
            por=LocationItem(name=tracking_results['location.por']),
            pod=LocationItem(name=tracking_results['location.pod']),
            pol=LocationItem(name=tracking_results['location.pol']),
            final_dest=LocationItem(name=tracking_results['Location.dest']),
            por_atd=tracking_results['departure.por_actual'],
            ata=tracking_results['arrival.pod_actual'],
            eta=tracking_results['arrival.pod_estimate'],
            atd=tracking_results['departure.pol_actual'],
            etd=tracking_results['departure.pol_estimate'],
            us_ams_status=customs_status['us_ams'],
            ca_aci_status=customs_status['canada_aci'],
            eu_ens_status=customs_status['eu_ens'],
            cn_cams_status=customs_status['china_cams'],
            ja_afr_status=customs_status['japan_afr'],
            freight_status=cargo_delivery_info['freight_status'],
            us_customs_status=cargo_delivery_info['us_customs_status'],
            deliv_order=cargo_delivery_info['delivery_order_status'],
            latest_update=latest_update,
            deliv_ata=cargo_delivery_info['delivery_order_time'],
            pol_ata=tracking_results['arrival.pol_actual'],
            firms_code=cargo_delivery_info['firm_code'],
            freight_date=cargo_delivery_info['freight_time'],
            us_customs_date=cargo_delivery_info['us_customs_time'],
            bl_type=cargo_delivery_info['bl_type'],
            way_bill_status=cargo_delivery_info['way_bill_status'],
            way_bill_date=cargo_delivery_info['way_bill_time'],
        )

        vessel = _Extractor.extract_vessel(response=response)
        yield VesselItem(
            vessel=vessel['vessel'],
            voyage=vessel['voyage'],
            pol=LocationItem(name=vessel['pol']),
            pod=LocationItem(name=vessel['pod']),
            ata=vessel['ata'],
            eta=vessel['eta'],
            atd=vessel['atd'],
            etd=vessel['etd'],
        )

        # parse other containers if there are many containers
        container_extractor = _ContainerExtractor()
        container_contents = container_extractor.extract_container_contents(response=response)
        h_num = -1
        for container_content in container_contents:
            if container_content.is_current:
                response.meta['container_content'] = container_content
                for item in self.parse_container(response=response):
                    yield item

            else:
                h_num -= 1
                container_url = self.url_factory.build_container_url(mbl_no=self.mbl_no)
                formdata = self.formdata_factory.build_container_formdata(
                    mbl_no=self.mbl_no, container_index=container_content.index, h_num=h_num,
                )

                yield scrapy.FormRequest(
                    url=container_url,
                    headers=self.headers,
                    formdata=formdata,
                    callback=self.parse_container,
                    meta={
                        'container_content': container_content,
                    },
                )

    @merge_yields
    def parse_container(self, response):
        container_content = response.meta['container_content']

        container_extractor = _ContainerExtractor()

        tracking_results = _Extractor.extract_tracking_results(response=response)
        container_info = container_extractor.extract_container_info(response=response, container_content=container_content)
        empty_return_location = _Extractor.extract_empty_return_location(response=response)
        container_status = list(_ContainerStatusExtractor.extract_container_status(response=response))

        container_item = ContainerItem(
                container_no=container_info['container_no'],
                last_free_day=container_info['lfd'],
                mt_location=LocationItem(name=empty_return_location['empty_return_location']),
                det_free_time_exp_date=empty_return_location['fdd'],
                por_etd=tracking_results['departure.por_estimate'],
                pol_eta=tracking_results['arrival.pol_estimate'],
                final_dest_eta=tracking_results['arrival.dest_estimate'],
                ready_for_pick_up=None,  # it may be assign in availability
        )

        # catch availability
        ava_exist = _Extractor.extract_availability_exist(response=response)
        if ava_exist:
            ava_formdata = self.formdata_factory.build_availability_formdata(
                mbl_no=self.mbl_no, container_no=container_content.container_no,
            )
            ava_url = self.url_factory.build_availability_url()

            yield scrapy.FormRequest(
                url=ava_url,
                headers=self.headers,
                formdata=ava_formdata,
                callback=self.parse_availability,
                meta={
                    'container_item': container_item,
                },
            )
        else:
            yield container_item

        for container in container_status:
            yield ContainerStatusItem(
                container_no=container_info['container_no'],
                description=container['status'],
                timestamp=container['date'],
                location=LocationItem(name=container['location']),
                transport=container['mode']
            )

    def parse_availability(self, response):
        container_item = response.meta['container_item']

        ready_for_pick_up = _AvailabilityExtractor.extract_availability(response)
        container_item['ready_for_pick_up'] = ready_for_pick_up
        yield container_item


class RedBlueTdExtractor(BaseTableCellExtractor):

    def extract(self, cell: Selector):
        red_text_list = [c.strip() for c in cell.css('span.font_red::text').getall()]
        blue_text_list = [c.strip() for c in cell.css('span.font_blue::text').getall()]
        return {
            'red': ' '.join(red_text_list) or None,
            'blue': ' '.join(blue_text_list) or None,
        }


class IgnoreDashTdExtractor(BaseTableCellExtractor):
    def extract(self, cell: Selector):
        td_text = cell.css('::text').get()
        text = td_text.strip() if td_text else ''
        return text if text != '-' else None


class _Extractor:
    @staticmethod
    def extract_tracking_results(response):
        table_selector = response.css('#trackingForm div.base_table01')[0]
        table_extractor = TableExtractor()
        table = table_extractor.extract(table=table_selector, locator=TopLeftHeaderTableLocator())
        red_blue_td_extractor = RedBlueTdExtractor()

        return {
            'location.por': table.extract_cell('Origin', 'Location'),
            'location.pol': table.extract_cell('Loading Port', 'Location'),
            'location.pod': table.extract_cell('Discharging Port', 'Location'),
            'Location.dest': table.extract_cell('Destination', 'Location'),
            'arrival.pol_estimate': table.extract_cell('Loading Port', 'Arrival', red_blue_td_extractor)['red'],
            'arrival.pol_actual': table.extract_cell('Loading Port', 'Arrival', red_blue_td_extractor)['blue'],
            'arrival.pod_estimate': table.extract_cell('Discharging Port', 'Arrival', red_blue_td_extractor)['red'],
            'arrival.pod_actual': table.extract_cell('Discharging Port', 'Arrival', red_blue_td_extractor)['blue'],
            'arrival.dest_estimate': table.extract_cell('Destination', 'Arrival', red_blue_td_extractor)['red'],
            'arrival.dest_actual': table.extract_cell('Destination', 'Arrival', red_blue_td_extractor)['blue'],
            'departure.por_estimate': table.extract_cell('Origin', 'Departure', red_blue_td_extractor)['red'],
            'departure.por_actual': table.extract_cell('Origin', 'Departure', red_blue_td_extractor)['blue'],
            'departure.pol_estimate': table.extract_cell('Loading Port', 'Departure', red_blue_td_extractor)['red'],
            'departure.pol_actual': table.extract_cell('Loading Port', 'Departure', red_blue_td_extractor)['blue'],
        }

    @staticmethod
    def extract_vessel(response):
        table_selector = response.css('#trackingForm div.base_table01')[3]
        table_extractor = TableExtractor()
        table = table_extractor.extract(table=table_selector, locator=TopHeaderTableLocator())
        red_blue_td_extractor = RedBlueTdExtractor()

        vessel_voyage_str = table.extract_cell('Vessel / Voyage', 0).split()
        vessel = ' '.join(vessel_voyage_str[:-1])
        voyage = vessel_voyage_str[-1]

        return {
            'vessel': vessel,
            'voyage': voyage,
            'pol': table.extract_cell('Loading Port', 0),
            'pod': table.extract_cell('Discharging Port', 0),
            'ata': table.extract_cell('Arrival', 0, red_blue_td_extractor)['blue'],
            'eta': table.extract_cell('Arrival', 0, red_blue_td_extractor)['red'],
            'atd': table.extract_cell('Departure', 0, red_blue_td_extractor)['blue'],
            'etd': table.extract_cell('Departure', 0, red_blue_td_extractor)['red'],
        }

    @staticmethod
    def extract_customs_status(response):
        table_selector = response.css('#trackingForm div.base_table01')[4]
        table_extractor = TableExtractor()
        table = table_extractor.extract(table=table_selector, locator=TopLeftHeaderTableLocator())

        return{
            'us_ams': table.extract_cell('US / AMS', 'Status') or None,
            'canada_aci': table.extract_cell('Canada / ACI', 'Status') or None,
            'eu_ens': table.extract_cell('EU / ENS', 'Status') or None,
            'china_cams': table.extract_cell('China / CAMS', 'Status') or None,
            'japan_afr': table.extract_cell('Japan / AFR', 'Status') or None,
        }

    @staticmethod
    def extract_cargo_delivery_info(response):
        table_selector = response.css('#trackingForm div.left_table01')[1]
        table_extractor = TableExtractor()
        table = table_extractor.extract(table=table_selector, locator=LeftHeaderTableLocator())

        if table.has_header(left='Way Bill'):
            bl_type = 'Way Bill'
            way_bill_status = table.extract_cell(0, 'Way Bill')
            way_bill_time = table.extract_cell(1, 'Way Bill')
        elif table.has_header(left='Original B/L'):
            bl_type = None
            way_bill_status = None
            way_bill_time = None
        else:
            raise CarrierResponseFormatError('Cargo Delivery Information Change!!!')

        return {
            'bl_type': bl_type,
            'way_bill_status': way_bill_status,
            'way_bill_time': way_bill_time,
            'freight_status': table.extract_cell(0, 'Freight'),
            'freight_time': table.extract_cell(1, 'Freight') or None,
            'us_customs_status': table.extract_cell(0, 'US Customs'),
            'us_customs_time': table.extract_cell(1, 'US Customs') or None,
            'firm_code': table.extract_cell(0, 'Firms Code'),
            'delivery_order_status': table.extract_cell(0, 'Delivery Order'),
            'delivery_order_time': table.extract_cell(1, 'Delivery Order') or None,
        }

    @staticmethod
    def extract_empty_return_location(response):
        table_selector = response.css('#trackingForm div.left_table01')[2]
        table_extractor = TableExtractor()
        table = table_extractor.extract(table=table_selector, locator=LeftHeaderTableLocator())
        fdd = table.extract_cell(0, 'Detention Freetime Expiry Date', extractor=IgnoreDashTdExtractor())

        return {
            'empty_return_location': table.extract_cell(0, 'Empty Container Return Location'),
            'fdd': fdd,
        }

    @staticmethod
    def extract_lastest_update(response):
        latest_update = ' '.join(response.css('p.text_type02::text')[-1].get().split()[-6:])
        return latest_update
    
    @staticmethod
    def extract_error_message(response):
        err_message = response.css('div#trackingForm p.text_type03::text').get()
        return err_message

    @staticmethod
    def extract_availability_exist(response):
        ava_exist = response.xpath('//a[text()="Container Availability"]').get()
        return bool(ava_exist)


@dataclasses.dataclass
class ContainerContent:
    container_no: str
    index: int
    is_current: bool


class _ContainerExtractor:
    @staticmethod
    def _get_conatiner_table(response):
        container_table = response.css('#trackingForm div.base_table01')[1]
        return container_table

    def extract_container_contents(self, response):
        table_selector = self._get_conatiner_table(response=response)
        container_selectors = table_selector.css('tbody tr')

        container_contents = []
        for index, selector in enumerate(container_selectors):
            container_no = selector.css('a::text').get()
            is_current = bool(selector.css('a[class="redBoldLink"]').get())
            container_contents.append(ContainerContent(
                container_no=container_no,
                index=index,
                is_current=is_current,
            ))
        return container_contents

    def extract_container_info(self, response, container_content: ContainerContent):
        table_selector = self._get_conatiner_table(response=response)
        table_extractor = TableExtractor()
        table = table_extractor.extract(table=table_selector, locator=TopHeaderTableLocator())
        index = container_content.index

        if table.has_header(top='Last Free Day (Basic)'):
            lfd = table.extract_cell('Last Free Day (Basic)', index)
        else:
            lfd = None

        return {
            'container_no': table.extract_cell('Container No.', index, extractor=FirstTextTdExtractor('a::text')),
            'type/size': table.extract_cell('Cntr Type/Size', index),
            'lfd': lfd,
        }


class _ContainerStatusExtractor:
    @staticmethod
    def extract_container_status(response):
        table_selector = response.css('#trackingForm div.base_table01')[5]
        table_extractor = TableExtractor()
        table = table_extractor.extract(table=table_selector, locator=TopHeaderTableLocator())

        for index, tr in enumerate(table_selector.css('tbody tr')):
            date = table.extract_cell('Date', index)
            time = table.extract_cell('Time', index)
            location = table.extract_cell('Location', index, extractor=IgnoreDashTdExtractor())
            mode = table.extract_cell('Mode', index, extractor=IgnoreDashTdExtractor())

            yield {
                'date': f'{date} {time}',
                'location': location,
                'status': table.extract_cell('Status Description', index),
                'mode': mode,
            }


class _AvailabilityExtractor:
    @staticmethod
    def extract_availability(response):
        table_selector = response.css('table.ty03')
        table_extractor = TableExtractor()
        table = table_extractor.extract(table=table_selector, locator=TopHeaderTableLocator())
        return table.extract_cell('STATUS', 0)
