from typing import List

from crawler.core_carrier.request_helpers import RequestOption
from crawler.spiders.carrier_sudu import MblState, VoyageSpec, ContainerDetailRoutingRule


def verify(results: List):
    assert isinstance(results[0], RequestOption)
    assert results[0].rule_name == ContainerDetailRoutingRule.name
    assert results[0].meta == {
        'mbl_no': 'SUDUN9998ALTNBPS',
        'container_key': 'j_idt6:searchForm:j_idt26:j_idt29:1:contDetailsLink',
        'voyage_spec': VoyageSpec(
            direction='Departure',
            container_key='j_idt6:searchForm:j_idt26:j_idt29:1:contDetailsLink',
            voyage_key='j_idt6:searchForm:j_idt39:j_idt113:5:voyageDetailsLink',
            location='Shanghai CNSHA',
            container_no='MSKU1906021',
        ),
        'mbl_state': MblState.MULTIPLE,
    }
