from typing import List

from crawler.core_carrier.request_helpers import RequestOption


def verify(results: List):
    assert isinstance(results[0], RequestOption)
    assert results[0].rule_name == 'TOKEN'
    assert results[0].meta['handle_httpstatus_list'] == [404]
    assert results[0].meta['mbl_no'] == '2634031060'

