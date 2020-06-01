from crawler.core_carrier.request_helpers import RequestOption
from crawler.spiders.carrier_sudu import VoyageRoutingRule, MblState


def verify(results, queue):
    assert len(results) == 1

    assert isinstance(results[0], RequestOption)
    assert results[0].rule_name == VoyageRoutingRule.name
    assert results[0].meta == {
        'mbl_state': MblState.MULTIPLE,
        'mbl_no': 'SUDUN9998ALTNBPS',
        'voyage_location': 'Shanghai CNSHA',
        'voyage_direction': 'Departure',
    }

    assert queue.qsize() == 0
