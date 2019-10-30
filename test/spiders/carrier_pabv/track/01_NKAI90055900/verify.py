from crawler.core_carrier.items import MblItem, LocationItem, VesselItem, ContainerItem, ContainerStatusItem


class Verifier:
    def verify(self, results):
        assert results[0] == MblItem(
            mbl_no='NKAI90055900',
            place_of_deliv=LocationItem(name='LOS'),
            por=LocationItem(name='NANJING'),
        )

        assert results[1] == VesselItem(
            vessel_key='DE LIN',
            etd='2019-06-21',
            pol='NANJING',
            vessel='DE LIN',
            voyage='XDEL0120N',
            pod='CNSHA',
            eta='2019-06-24',
        )
        assert results[2] == VesselItem(
            vessel_key='COSCO SPAIN',
            etd='2019-06-29',
            pol='SHANGHAI',
            vessel='COSCO SPAIN',
            voyage='VCSP0029E',
            pod='USLAX',
            eta='2019-07-18',
        )

        assert results[3] == ContainerItem(
            container_key='PCIU9477648',
            container_no='PCIU9477648',
        )
