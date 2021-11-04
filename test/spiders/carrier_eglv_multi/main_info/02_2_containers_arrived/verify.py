from crawler.core_carrier.items import MblItem, LocationItem, ContainerItem
from crawler.core_carrier.request_helpers import RequestOption
from crawler.spiders.carrier_eglv import ContainerStatusRoutingRule


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
            etd='JUL-17-2019',
            final_dest=LocationItem(name=None),
            eta=None,
            cargo_cutoff_date=None,
            task_id='1',
        )

        assert results[1] == ContainerItem(
            container_key='GAOU6281170',
            container_no='GAOU6281170',
            task_id='1',
        )

        assert isinstance(results[2], RequestOption)
        assert results[2].rule_name == ContainerStatusRoutingRule.name
        assert results[2].meta == {
            'container_no': 'GAOU6281170',
            'task_id': '1',
        }

        assert results[3] == ContainerItem(
            container_key='FCIU9351388',
            container_no='FCIU9351388',
            task_id='1',
        )

        assert isinstance(results[4], RequestOption)
        assert results[4].rule_name == ContainerStatusRoutingRule.name
        assert results[4].meta == {
            'container_no': 'FCIU9351388',
            'task_id': '1',
        }
