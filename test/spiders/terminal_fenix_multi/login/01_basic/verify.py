from typing import List

from crawler.core_terminal.request_helpers import RequestOption
from crawler.core_terminal.voyagecontrol_share_spider import ListTracedContainerRoutingRule
from crawler.spiders.terminal_fenix_multi import TerminalFenixSpider


def verify(results: List):
    assert isinstance(results[0], RequestOption)
    assert results[0].rule_name == ListTracedContainerRoutingRule.name
    assert results[0].meta == {
        "is_first": True,
        "container_nos": ["HMMU6487200"],
        "authorization_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjo1NTU4MSwidXNlcm5hbWUiOiJoYXJkMjAyMDA2MDEwQGdtYWlsLmNvbSIsImV4cCI6MTYzMDA0NzYwNywiZW1haWwiOiJoYXJkMjAyMDA2MDEwQGdtYWlsLmNvbSJ9.LGxtdSAwiR0e3ykqwWezxjHCll250cg13ikf-_s4iGQ",
        "company_info": TerminalFenixSpider.company_info,
    }
