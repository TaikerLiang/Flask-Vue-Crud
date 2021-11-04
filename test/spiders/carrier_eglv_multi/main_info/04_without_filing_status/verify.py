from crawler.core_carrier.items import MblItem, LocationItem, ContainerItem
from crawler.core_carrier.request_helpers import RequestOption
from crawler.spiders.carrier_eglv import ReleaseStatusRoutingRule, ContainerStatusRoutingRule


class Verifier:
    def verify(self, results):
        assert results[0] == MblItem(
            mbl_no='100980089898',
            vessel='EVER LYRIC',
            voyage='1010-032E',
            por=LocationItem(name='LUDHIANA (IN)'),
            pol=LocationItem(name='MUNDRA (IN)'),
            pod=LocationItem(name='LOS ANGELES, CA (US)'),
            place_of_deliv=LocationItem(name='LONG BEACH, CA (US)'),
            etd='NOV-27-2019',
            final_dest=LocationItem(name=None),
            eta='JAN-01-2020',
            cargo_cutoff_date='NOV-22-2019 17:30',
            task_id='1',
        )

        assert results[1] == ContainerItem(
            container_key='EISU3983490',
            container_no='EISU3983490',
            task_id='1',
        )

        assert isinstance(results[2], RequestOption)
        assert results[2].rule_name == ContainerStatusRoutingRule.name
        assert results[2].meta == {
            'container_no': 'EISU3983490',
            'task_id': '1',
        }

        assert isinstance(results[3], RequestOption)
        assert results[3].rule_name == ReleaseStatusRoutingRule.name
