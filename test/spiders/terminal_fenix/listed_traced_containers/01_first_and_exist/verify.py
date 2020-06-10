from typing import List

from crawler.core_terminal.request_helpers import RequestOption
from crawler.spiders.terminal_fenix import DelContainerFromTraceRoutingRule


def verify(results: List):
    assert isinstance(results[0], RequestOption)
    assert results[0].rule_name == DelContainerFromTraceRoutingRule.name
    assert results[0].meta == {
        'container_no': 'TCNU6056527',
        'authorization_token': '',
        'not_finished': True,
    }

