from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.spiders.terminal_v136 import LoginRoutingRule
from test.spiders.terminal_v136 import login


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=login, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    "sub,container_no,",
    [
        ("01_basic", "EITU1744546"),
    ],
)
def test_login_routing_rule(sub, container_no, sample_loader):
    httptext = sample_loader.read_file(sub, "sample.html")

    request_option = LoginRoutingRule.build_request_option(container_no_list=[container_no])

    response = TextResponse(
        url=request_option.url,
        body=httptext,
        encoding="utf-8",
        request=Request(
            url=request_option.url,
            meta=request_option.meta,
        ),
    )

    rule = LoginRoutingRule()
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verify_module.verify(results=results)
