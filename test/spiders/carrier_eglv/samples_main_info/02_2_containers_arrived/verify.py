from scrapy import FormRequest

from crawler.core_carrier.items import MblItem, LocationItem, ContainerItem


class Verifier:

    def verify(self, results):
        assert results[0] == MblItem(
            mbl_no='003901793951',
            vessel=None,
            voyage=None,
            por=LocationItem(name='TAICHUNG (TW)'),
            pol=LocationItem(name='KAOHSIUNG (TW)'),
            pod=LocationItem(name='BALTIMORE, MD (US)'),
            place_of_deliv=LocationItem(name='BALTIMORE, MD (US)'),
            est_onboard_date='JUL-17-2019',
            final_dest=LocationItem(name=None),
            eta=None,
            cargo_cutoff_date=None,
        )

        assert results[1] == ContainerItem(
            container_no='GAOU6281170',
        )

        assert isinstance(results[2], FormRequest)
        assert results[2].url == 'https://www.shipmentlink.com/servlet/TDB1_CargoTracking.do'
        assert results[2].meta == {
            'CARRIER_CORE_RULE_NAME': 'CONTAINER_STATUS',
            'container_no': 'GAOU6281170',
        }

        assert results[3] == ContainerItem(
            container_no='FCIU9351388',
        )

        assert isinstance(results[4], FormRequest)
        assert results[4].meta == {
            'CARRIER_CORE_RULE_NAME': 'CONTAINER_STATUS',
            'container_no': 'FCIU9351388',
        }
