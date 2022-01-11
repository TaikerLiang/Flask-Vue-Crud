from typing import List

from crawler.core_terminal.items import TerminalItem
from crawler.core_terminal.request_helpers import RequestOption
from crawler.core_terminal.voyagecontrol_share_spider import DelContainerFromTraceRoutingRule
from crawler.spiders.terminal_yti_multi import TerminalYtiSpider


def verify(results: List):
    assert results[0] == TerminalItem(
        container_no="HAMU1174866",
        ready_for_pick_up="Unavailable",
        appointment_date="",
        last_free_day="08/19/2021 12:00:00 AM",
        demurrage="",
        holds="",
        cy_location="",
        customs_release="RELEASED",
        carrier_release="RELEASED",
    )

    assert isinstance(results[1], RequestOption)
    assert results[1].rule_name == DelContainerFromTraceRoutingRule.name
    assert results[1].meta == {
        "container_nos": ["HAMU1174866"],
        "authorization_token": "",
        "not_finished": False,
        "company_info": TerminalYtiSpider.company_info,
    }
