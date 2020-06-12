from typing import List

from crawler.core_terminal.request_helpers import RequestOption
from crawler.spiders.terminal_fenix import AddContainerToTraceRoutingRule


def verify(results: List):
    assert isinstance(results[0], RequestOption)
    assert results[0].rule_name == AddContainerToTraceRoutingRule.name
    assert results[0].meta == {
        'container_no': 'CAIU7086501',
        'authorization_token': '',
        'dont_retry': True,
        'handle_httpstatus_list': [502],
    }


