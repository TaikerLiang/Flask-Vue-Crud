from crawler.core_carrier.items import MblItem, LocationItem, ContainerItem
from crawler.core_carrier.request_helpers import RequestOption
from crawler.spiders.carrier_eglv import ContainerStatusRoutingRule, FilingStatusRoutingRule, ReleaseStatusRoutingRule


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
            etd='AUG-18-2019',
            eta='SEP-25-2019',
            cargo_cutoff_date=None,
        )

        assert results[1] == ContainerItem(
            container_key='HMCU9173542',
            container_no='HMCU9173542',
        )

        assert isinstance(results[2], RequestOption)
        assert results[2].rule_name == ContainerStatusRoutingRule.name
        assert results[2].meta == {
            'container_no': 'HMCU9173542',
        }
        assert results[2].form_data == {
            'bl_no': '003902245109',
            'cntr_no': 'HMCU9173542',
            'onboard_date': '20190818',
            'pol': 'TWKSG',
            'pod': 'USBOS',
            'podctry': 'US',
            'TYPE': 'CntrMove',
        }

        assert results[3] == ContainerItem(
            container_key='EITU1111240',
            container_no='EITU1111240',
        )

        assert isinstance(results[4], RequestOption)
        assert results[4].rule_name == ContainerStatusRoutingRule.name
        assert results[4].meta == {
            'container_no': 'EITU1111240',
        }
        assert results[4].form_data == {
            'bl_no': '003902245109',
            'cntr_no': 'EITU1111240',
            'onboard_date': '20190818',
            'pol': 'TWKSG',
            'pod': 'USBOS',
            'podctry': 'US',
            'TYPE': 'CntrMove',
        }

        assert isinstance(results[7], RequestOption)
        assert results[7].rule_name == FilingStatusRoutingRule.name
        assert results[7].form_data == {
            'TYPE': 'GetDispInfo',
            'Item': 'AMSACK',
            'BL': '003902245109',
            'firstCtnNo': 'HMCU9173542',
            'pod': 'USBOS',
        }

        assert isinstance(results[8], RequestOption)
        assert results[8].rule_name == ReleaseStatusRoutingRule.name
        assert results[8].form_data == {
            'TYPE': 'GetDispInfo',
            'Item': 'RlsStatus',
            'BL': '003902245109',
        }

