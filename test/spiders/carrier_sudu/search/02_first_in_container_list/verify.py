from typing import List

from scrapy import Request


def verify(results: List):
    assert isinstance(results[0], Request)
    assert results[0].meta == {
        'CARRIER_CORE_RULE_NAME': 'Search',
        'mbl_no': 'SUDUN9998ALTNBPS',
        'expect_view': 'CONTAINER_DETAIL',
        'is_first_process': False,
    }
