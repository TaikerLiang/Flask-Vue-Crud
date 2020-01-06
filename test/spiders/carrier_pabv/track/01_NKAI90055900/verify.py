from crawler.core_carrier.items import MblItem, LocationItem, VesselItem, ContainerItem
from crawler.spiders.carrier_pabv import ContainerRoutingRule


class Verifier:
    def verify(self, results):
        assert results[0] == MblItem(
            mbl_no='NKAI90055900',
            place_of_deliv=LocationItem(name='LOS ANGELES', un_lo_code='USLAX'),
            por=LocationItem(name='NANJING', un_lo_code='CNNKG'),
        )

        assert results[1] == VesselItem(
            vessel_key='DE LIN',
            vessel='DE LIN',
            voyage='XDEL0120N',
            pol=LocationItem(name='NANJING', un_lo_code='CNNKG'),
            pod=LocationItem(un_lo_code='CNSHA'),
            etd='2019-06-21',
            eta='2019-06-24',
        )
        assert results[2] == VesselItem(
            vessel_key='COSCO SPAIN',
            vessel='COSCO SPAIN',
            voyage='VCSP0029E',
            pol=LocationItem(name='SHANGHAI', un_lo_code='CNSHA'),
            pod=LocationItem(un_lo_code='USLAX'),
            etd='2019-06-29',
            eta='2019-07-18',
        )

        assert results[3] == ContainerItem(
            container_key='PCIU9477648',
            container_no='PCIU9477648',
        )

        assert results[4] == ContainerRoutingRule.build_request_option(
            mbl_no='NKAI90055900',
            cookies={},
            container_id='PCIU9477648',
        )
