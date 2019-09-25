from scrapy import FormRequest

from crawler.core_carrier.items import MblItem, LocationItem, ContainerItem
from test.spiders.utils import convert_formdata_to_bytes


class Verifier:

    def verify(self, results):
        assert results[0] == MblItem(
            mbl_no='003902245109',
            vessel='EVER LIVEN',
            voyage='0915-038E',
            por=LocationItem(name='KAOHSIUNG (TW)'),
            pol=LocationItem(name='KAOHSIUNG (TW)'),
            pod=LocationItem(name='BOSTON, MA (US)'),
            place_of_deliv=LocationItem(name='BOSTON, MA (US)'),
            final_dest=LocationItem(name=None),
            est_onboard_date='AUG-18-2019',
            eta='SEP-25-2019',
            cargo_cutoff_date=None,
        )

        assert results[1] == ContainerItem(
            container_no='HMCU9173542',
        )

        assert isinstance(results[2], FormRequest)
        assert results[2].url == 'https://www.shipmentlink.com/servlet/TDB1_CargoTracking.do'
        assert results[2].meta == {
            'CARRIER_CORE_RULE_NAME': 'CONTAINER_STATUS',
            'container_no': 'HMCU9173542',
        }
        assert results[2].body == convert_formdata_to_bytes(
            formdata={
                'bl_no': '003902245109',
                'cntr_no': 'HMCU9173542',
                'onboard_date': '20190818',
                'pol': 'TWKSG',
                'pod': 'USBOS',
                'podctry': 'US',
                'TYPE': 'CntrMove',
                }
        )

        assert results[3] == ContainerItem(
            container_no='EITU1111240',
        )

        assert isinstance(results[4], FormRequest)
        assert results[4].meta == {
            'CARRIER_CORE_RULE_NAME': 'CONTAINER_STATUS',
            'container_no': 'EITU1111240',
        }
        assert results[4].body == convert_formdata_to_bytes(
            formdata={
                'bl_no': '003902245109',
                'cntr_no': 'EITU1111240',
                'onboard_date': '20190818',
                'pol': 'TWKSG',
                'pod': 'USBOS',
                'podctry': 'US',
                'TYPE': 'CntrMove',
            }
        )

        assert results[7].meta == {
            'CARRIER_CORE_RULE_NAME': 'FILING_STATUS',
        }
        assert results[7].body == convert_formdata_to_bytes(
            formdata={
                'TYPE': 'GetDispInfo',
                'Item': 'AMSACK',
                'BL': '003902245109',
                'firstCtnNo': 'HMCU9173542',
                'pod': 'USBOS',
            }
        )

        assert results[8].meta == {
            'CARRIER_CORE_RULE_NAME': 'RELEASE_STATUS',
        }
        assert results[8].body == convert_formdata_to_bytes(
            formdata={
                'TYPE': 'GetDispInfo',
                'Item': 'RlsStatus',
                'BL': '003902245109',
            }
        )
