from typing import List

from crawler.core_terminal.request_helpers import RequestOption
from crawler.spiders.terminal_fenix import ListTracedContainerRoutingRule


def verify(results: List):
    assert isinstance(results[0], RequestOption)
    assert results[0].rule_name == ListTracedContainerRoutingRule.name
    assert results[0].meta == {
        'is_first': True,
        'container_no': 'CAIU7086501',
        'authorization_token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6ImhhcmQyMDIwMDYwMTBAZ21haWwuY29tIi'
                               'widXNlcl9pZCI6NTU1ODEsImVtYWlsIjoiaGFyZDIwMjAwNjAxMEBnbWFpbC5jb20iLCJleHAiOjE1OTE2MDk2M'
                               'zR9.LUrqPIKqbkxTX1HM6irPpgQh9b1Sls9-8u9ppqZXzaU',
    }


