from typing import List

from crawler.core_carrier.request_helpers import RequestOption


def verify(results: List):
    assert isinstance(results[0], RequestOption)
    assert results[0].rule_name == 'COOKIES'
    assert results[0].headers == {
        'X-AA-Challenge': '259649',
        'X-AA-Challenge-ID': '1719173',
        'X-AA-Challenge-Result': '778698104',
        'Content-Type': 'text/plain',
    }



