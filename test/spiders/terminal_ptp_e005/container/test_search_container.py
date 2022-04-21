from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_terminal.propassva_ptp_share_spider import GetContainerNoRoutingRule
from test.spiders.terminal_ptp_e005 import container


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=container, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    "sub, container_no_list",
    [
        ("01_basic", ["TCKU7313610", "MSDU8213580", "MAGU5304736"]),
        ("e01_invalid_container_no", ["TGCU0160986"]),
    ],
)
def test_container_handle(sub, container_no_list, sample_loader):
    httptext = sample_loader.read_file(sub, "sample.json")

    option = GetContainerNoRoutingRule.build_request_option(
        container_no_list=container_no_list,
        auth="",
        first=False,
    )
    response = TextResponse(
        url=option.url,
        body=httptext,
        encoding="utf-8",
        request=Request(
            url=option.url,
            meta=option.meta,
        ),
    )
    rule = GetContainerNoRoutingRule()
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verify_module.verify(results=results)
