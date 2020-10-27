from typing import List

from crawler.core_terminal.request_helpers import RequestOption
from crawler.spiders.terminal_tti import SearchContainerRoutingRule, SearchMblRoutingRule


def verify(results: List):
    assert isinstance(results[0], RequestOption)
    assert results[0].rule_name == SearchContainerRoutingRule.name

    assert isinstance(results[1], RequestOption)
    assert results[1].rule_name == SearchMblRoutingRule.name



