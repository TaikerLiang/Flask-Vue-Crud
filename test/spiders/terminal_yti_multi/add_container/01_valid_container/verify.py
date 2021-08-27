from typing import List

from crawler.core_terminal.request_helpers import RequestOption
from crawler.core_terminal.voyagecontrol_share_spider import ListTracedContainerRoutingRule
from crawler.spiders.terminal_yti_multi import TerminalYtiSpider

def verify(results: List):
    assert isinstance(results[0], RequestOption)
    assert results[0].rule_name == ListTracedContainerRoutingRule.name
    assert results[0].meta == {
        'is_first': False,
        'container_no': 'CAIU7086501',
        'authorization_token': '',
        'company_info': TerminalYtiSpider.company_info,
    }
