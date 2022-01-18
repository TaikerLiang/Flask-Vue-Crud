from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_terminal.voyagecontrol_share_spider import ListTracedContainerRoutingRule
from crawler.spiders.terminal_voyagecontrol_y257 import TerminalFenixSpider
from test.spiders.terminal_voyagecontrol_y257 import listed_traced_containers


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=listed_traced_containers, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    "sub,container_no,is_first",
    [
        ("01_first_and_exist", "TGHU6651727", True),
        ("02_first_and_not_exist", "FBLU0255200", True),
    ],
)
def test_container_handle(sub, container_no, is_first, sample_loader):
    json_text = sample_loader.read_file(sub, "sample.json")

    option = ListTracedContainerRoutingRule.build_request_option(
        container_nos=[container_no],
        authorization_token="",
        company_info=TerminalFenixSpider.company_info,
        is_first=is_first,
    )

    response = TextResponse(
        url=option.url,
        body=json_text,
        encoding="utf-8",
        request=Request(
            url=option.url,
            meta={
                "is_first": is_first,
                "container_nos": [container_no],
                "authorization_token": "",
                "company_info": TerminalFenixSpider.company_info,
            },
        ),
    )

    rule = ListTracedContainerRoutingRule()
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verify_module.verify(results=results)
