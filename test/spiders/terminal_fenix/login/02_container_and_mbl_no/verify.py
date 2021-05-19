from typing import List

from crawler.core_terminal.request_helpers import RequestOption
from crawler.spiders.terminal_fenix import ListTracedContainerRoutingRule, SearchMblRoutingRule


def verify(results: List):
    assert isinstance(results[0], RequestOption)
    assert results[0].rule_name == ListTracedContainerRoutingRule.name
    assert results[0].meta == {
        'is_first': True,
        'container_no': 'TCNU6056527',
        'authorization_token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6ImhhcmQyMDIwMDYwMTBAZ21haWwuY29tIi'
        'widXNlcl9pZCI6NTU1ODEsImVtYWlsIjoiaGFyZDIwMjAwNjAxMEBnbWFpbC5jb20iLCJleHAiOjE1OTE2MDkzN'
        'jB9._xAvY-8mLIOXCC5TnfudKvvY2KGJ6nsocdov9f7sPBY',
    }

    assert isinstance(results[1], RequestOption)
    assert results[1].rule_name == SearchMblRoutingRule.name
    assert results[1].meta == {
        'handle_httpstatus_list': [404],
        'mbl_no': '2638732540',
    }
