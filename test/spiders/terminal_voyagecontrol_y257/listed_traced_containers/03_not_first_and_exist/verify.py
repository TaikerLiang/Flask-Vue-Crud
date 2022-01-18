from typing import List

from crawler.core_terminal.items import TerminalItem
from crawler.core_terminal.request_helpers import RequestOption
from crawler.core_terminal.voyagecontrol_share_spider import DelContainerFromTraceRoutingRule
from crawler.spiders.terminal_voyagecontrol_y257 import TerminalFenixSpider


def verify(results: List):
    assert results[0] == TerminalItem(
        container_no="TCNU1794174",
        ready_for_pick_up="OnHold",
        appointment_date="CUSTOMS",
        last_free_day="2021-Sep-01",
        demurrage="0.0",
        holds="CUSTOMS",
        cy_location="FF17",
        customs_release="HOLD",
        carrier_release="",
    )

    assert isinstance(results[1], RequestOption)
    assert results[1].rule_name == DelContainerFromTraceRoutingRule.name
    assert results[1].meta == {
        "container_nos": ["TCNU1794174"],
        "authorization_token": "",
        "not_finished": False,
        "company_info": TerminalFenixSpider.company_info,
    }
