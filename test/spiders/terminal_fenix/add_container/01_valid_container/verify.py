from typing import List

from crawler.core_terminal.request_helpers import RequestOption
from crawler.spiders.terminal_fenix import ListTracedContainerRoutingRule


def verify(results: List):
    assert isinstance(results[0], RequestOption)
    assert results[0].rule_name == ListTracedContainerRoutingRule.name
    assert results[0].meta == {
        'is_first': False,
        'container_no': 'CAIU7086501',
        'authorization_token': '',
    }
