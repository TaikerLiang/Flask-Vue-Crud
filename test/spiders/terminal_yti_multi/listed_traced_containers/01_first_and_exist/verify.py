from typing import List

from crawler.core_terminal.request_helpers import RequestOption
from crawler.core_terminal.voyagecontrol_share_spider import DelContainerFromTraceRoutingRule
from crawler.spiders.terminal_yti_multi import TerminalYtiSpider


def verify(results: List):
    assert isinstance(results[0], RequestOption)
    assert results[0].rule_name == DelContainerFromTraceRoutingRule.name
    assert results[0].meta == {
        "container_nos": ["BSIU9653301"],
        "authorization_token": "",
        "not_finished": True,
        "company_info": TerminalYtiSpider.company_info,
    }
