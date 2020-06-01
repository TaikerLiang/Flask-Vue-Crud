from typing import List

from crawler.core_carrier.request_helpers import RequestOption
from crawler.spiders.carrier_sudu import MblState, MblSearchResultRoutingRule


def verify_output(results: List):
    assert isinstance(results[0], RequestOption)
    assert results[0].rule_name == MblSearchResultRoutingRule.name
    assert results[0].meta == {
        'mbl_no': 'SUDUN9998ALTNBPS',
        'mbl_state': MblState.MULTIPLE,
    }


def verify_local_variable(routing_rule: MblSearchResultRoutingRule):
    assert routing_rule._containers_set == {'MRKU0161647', 'MSKU1906021'}
