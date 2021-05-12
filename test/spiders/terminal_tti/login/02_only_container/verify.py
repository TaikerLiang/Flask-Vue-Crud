from typing import List

from crawler.core_terminal.request_helpers import RequestOption
from crawler.spiders.terminal_tti import SearchContainerRoutingRule


def verify(results: List):
    assert isinstance(results[0], RequestOption)
    assert results[0].rule_name == SearchContainerRoutingRule.name

    assert len(results) == 1
