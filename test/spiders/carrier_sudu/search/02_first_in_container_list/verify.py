from typing import List

from crawler.core_carrier.rules import RoutingRequest


def verify(results: List):
    assert isinstance(results[0], RoutingRequest)
    assert results[0].request.meta == {
        'mbl_no': 'SUDUN9998ALTNBPS',
        'expect_view': 'CONTAINER_DETAIL',
        'is_first_process': False,
    }
