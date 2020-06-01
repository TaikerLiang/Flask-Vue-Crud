from typing import List

from crawler.core_carrier.request_helpers import RequestOption
from crawler.spiders.carrier_sudu import MblState, VoyageRoutingRule


def verify(results: List):
    assert isinstance(results[0], RequestOption)
    assert results[0].rule_name == VoyageRoutingRule.name
    assert results[0].meta == {
        'mbl_no': 'SUDUN0498AQEP33P',
        'mbl_state': MblState.SINGLE,
        'voyage_location': 'Xingang CNXIG',
        'voyage_direction': 'Departure',
    }
