from typing import List

from crawler.core_terminal.request_helpers import RequestOption
from crawler.core_terminal.voyagecontrol_share_spider import AddContainerToTraceRoutingRule
from crawler.spiders.terminal_fenix_multi import TerminalFenixSpider

def verify(results: List):
    assert isinstance(results[0], RequestOption)
    assert results[0].rule_name == AddContainerToTraceRoutingRule.name
    assert results[0].meta == {
        'container_no': 'FBLU0255200',
        'authorization_token': '',
        'dont_retry': True,
        'company_info': TerminalFenixSpider.company_info,
        'handle_httpstatus_list': [502],
    }
