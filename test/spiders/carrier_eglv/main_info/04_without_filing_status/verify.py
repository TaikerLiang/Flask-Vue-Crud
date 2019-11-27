from scrapy import FormRequest

from crawler.core_carrier.items import MblItem, LocationItem, ContainerItem


class Verifier:

    def verify(self, results):
        assert results[0] == MblItem(
            mbl_no='100980089898',
            vessel='EVER LYRIC 1010',
            voyage='032E',
            por=LocationItem(name='LUDHIANA (IN)'),
            pol=LocationItem(name='MUNDRA (IN)'),
            pod=LocationItem(name='LOS ANGELES, CA (US)'),
            place_of_deliv=LocationItem(name='LONG BEACH, CA (US)'),
            est_onboard_date='NOV-27-2019',
            final_dest=LocationItem(name=None),
            eta='JAN-01-2020',
            cargo_cutoff_date='NOV-22-2019 17:30',
        )

        assert results[1] == ContainerItem(
            container_key='EISU3983490',
            container_no='EISU3983490',
        )

        assert isinstance(results[2], FormRequest)
        assert results[2].url == 'https://www.shipmentlink.com/servlet/TDB1_CargoTracking.do'
        assert results[2].meta == {
            'CARRIER_CORE_RULE_NAME': 'CONTAINER_STATUS',
            'container_no': 'EISU3983490',
        }

        assert results[3].meta != {
            'CARRIER_CORE_RULE_NAME': 'FILING_STATUS',
            'container_no': 'EISU3983490',
        }
