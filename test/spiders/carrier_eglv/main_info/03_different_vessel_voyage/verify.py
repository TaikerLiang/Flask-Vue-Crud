from scrapy import FormRequest

from crawler.core_carrier.items import MblItem, LocationItem, ContainerItem


class Verifier:

    def verify(self, results):
        assert results[0] == MblItem(
            mbl_no='142901393381',
            vessel=None,
            voyage=None,
            por=LocationItem(name='SHANGHAI (CN)'),
            pol=LocationItem(name='SHANGHAI (CN)'),
            pod=LocationItem(name='LONG BEACH, CA (US)'),
            place_of_deliv=LocationItem(name='LOS ANGELES, CA (US)'),
            etd='OCT-04-2019',
            final_dest=LocationItem(name=None),
            eta=None,
            cargo_cutoff_date=None,
        )

        assert results[1] == ContainerItem(
            container_key='TRIU8882058',
            container_no='TRIU8882058',
        )

        assert isinstance(results[2], FormRequest)
        assert results[2].url == 'https://www.shipmentlink.com/servlet/TDB1_CargoTracking.do'
        assert results[2].meta == {
            'CARRIER_CORE_RULE_NAME': 'CONTAINER_STATUS',
            'container_no': 'TRIU8882058',
        }
