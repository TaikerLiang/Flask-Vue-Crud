from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_terminal.ets_share_spider import LoginRoutingRule
from crawler.spiders.terminal_ets_pierce_county import TerminalPierceCountySpider
from test.spiders.terminal_ets import login


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=login, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    "sub,container_no",
    [
        ("01_basic", "EISU8049563"),
    ],
)
def test_login_handle(sub, container_no, sample_loader):
    json_text = sample_loader.read_file(sub, "sample.json")

    option = LoginRoutingRule.build_request_option(
        captcha_text="",
        container_no_list=[container_no],
        dc="",
        verify_key="",
        company_info=TerminalPierceCountySpider.company_info,
    )

    response = TextResponse(
        url=option.url,
        body=json_text,
        encoding="utf-8",
        request=Request(
            url=option.url,
            meta=option.meta,
        ),
    )

    rule = LoginRoutingRule()
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verify_module.verify(results=results)
