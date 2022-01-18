from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_terminal.tideworks_share_spider import LoginRoutingRule
from crawler.spiders.terminal_tideworks_q795 import TerminalTideworksNolSpider
from test.spiders.terminal_tideworks_q795 import login


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=login, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    "sub,container_no",
    [
        ("01_basic", "TRHU2178921"),
    ],
)
def test_login_handle(sub, container_no, sample_loader):
    html_text = sample_loader.read_file(sub, "sample.html")

    option = LoginRoutingRule.build_request_option(
        container_nos=[container_no],
        company_info=TerminalTideworksNolSpider.company_info,
    )

    response = TextResponse(
        url=option.url,
        body=html_text,
        encoding="utf-8",
        request=Request(
            url=option.url,
            headers={"Cookie": "test_cookie"},
            meta=option.meta,
        ),
    )

    rule = LoginRoutingRule()
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verify_module.verify(results=results)
