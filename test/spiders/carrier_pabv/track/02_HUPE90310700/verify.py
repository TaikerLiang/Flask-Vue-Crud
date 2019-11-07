from crawler.core_carrier.items import MblItem, LocationItem, VesselItem, ContainerItem


class Verifier:
    def verify(self, results):
        assert results[0] == MblItem(
            mbl_no='HUPE90310700',
            place_of_deliv=LocationItem(name='LONG BEACH', un_lo_code='USLGB'),
            por=LocationItem(name='XIAO LAN', un_lo_code='CNXAO'),
        )

        assert results[1] == VesselItem(
            vessel_key='ZHONG HANG 917',
            vessel='ZHONG HANG 917',
            voyage='XZH79927E',
            pol=LocationItem(name='XIAO LAN', un_lo_code='CNXAO'),
            pod=LocationItem(un_lo_code='CNNSA'),
            etd='2019-09-27',
            eta='2019-09-28',
        )
        assert results[2] == VesselItem(
            vessel_key='COSCO EUROPE',
            vessel='COSCO EUROPE',
            voyage='VQCE0070E',
            pol=LocationItem(name='NANSHA', un_lo_code='CNNSA'),
            pod=LocationItem(un_lo_code='USLGB'),
            etd='2019-10-12',
            eta='2019-10-28',
        )

        assert results[3] == ContainerItem(
            container_key='PCIU9006036',
            container_no='PCIU9006036',
        )
