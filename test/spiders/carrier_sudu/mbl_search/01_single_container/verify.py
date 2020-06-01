from typing import List

from crawler.core_carrier.request_helpers import RequestOption
from crawler.spiders.carrier_sudu import MblState, MblSearchResultRoutingRule, ContainerDetailRoutingRule


def verify_output(results: List):
    assert isinstance(results[0], RequestOption)
    assert results[0].rule_name == ContainerDetailRoutingRule.name
    assert results[0].meta == {
        'mbl_no': 'SUDUN0498AQEP33P',
        'container_key': '',
        'mbl_state': MblState.SINGLE,
        'voyage_spec': None,
    }


def verify_local_variable(routing_rule: MblSearchResultRoutingRule):
    assert routing_rule._containers_set == set()

