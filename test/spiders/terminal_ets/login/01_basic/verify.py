from typing import List

from crawler.core_terminal.request_helpers import RequestOption


def verify(results: List):
    assert isinstance(results[0], RequestOption)
    assert results[0].rule_name == 'CONTAINER'
    assert results[0].meta == {
        'container_no': 'EISU8049563',
        'sk': '6718442984',
    }

