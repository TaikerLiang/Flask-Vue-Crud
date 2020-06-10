from typing import List

from crawler.core_terminal.items import TerminalItem
from crawler.core_terminal.request_helpers import RequestOption
from crawler.spiders.terminal_fenix import DelContainerFromTraceRoutingRule


def verify(results: List):
    assert results[0] == TerminalItem(
        container_no='CAIU7086501',
        ready_for_pick_up='Unavailable',
        appointment_date=None,
        last_free_day='Invalid date',
        demurrage=None,
        holds=None,
        cy_location='On Vessel',
    )

    assert isinstance(results[1], RequestOption)
    assert results[1].rule_name == DelContainerFromTraceRoutingRule.name
    assert results[1].meta == {
        'container_no': 'CAIU7086501',
        'authorization_token': '',
        'not_finished': False,
    }

