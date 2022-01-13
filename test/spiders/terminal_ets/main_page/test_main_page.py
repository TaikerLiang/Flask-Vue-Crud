from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_terminal.ets_share_spider import MainPageRoutingRule
from crawler.spiders.terminal_ets_y124 import TerminalEtsBerthSpider
from test.spiders.terminal_ets import main_page


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=main_page, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    "sub,container_no",
    [
        ("01_basic", "EISU8049563"),
    ],
)
def test_main_page_handle(sub, container_no, sample_loader):
    html_text = sample_loader.read_file(sub, "sample.html")

    option = MainPageRoutingRule.build_request_option(
        container_no_list=[container_no],
        company_info=TerminalEtsBerthSpider.company_info,
    )

    response = TextResponse(
        url=option.url,
        body=html_text,
        encoding="utf-8",
        request=Request(
            url=option.url,
            meta=option.meta,
        ),
    )

    rule = MainPageRoutingRule()
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verify_module.verify(results=results)
