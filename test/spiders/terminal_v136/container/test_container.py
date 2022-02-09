from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.spiders.terminal_v136 import ContainerRoutingRule
from test.spiders.terminal_v136 import container


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=container, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    "sub,container_no,",
    [
        ("01_basic", "EITU1744546"),
        ("02_with_lfd", "APZU3951656"),
        ("03_data_not_found", "TCNU5087312"),
    ],
)
def test_container_routing_rule(sub, container_no, sample_loader):
    json_text = sample_loader.read_file(sub, "sample.json")

    request_option = ContainerRoutingRule.build_request_option(
        container_no_list=[container_no],
    )

    response = TextResponse(
        url=request_option.url,
        body=json_text,
        encoding="utf-8",
        request=Request(
            url=request_option.url,
            meta=request_option.meta,
        ),
    )

    rule = ContainerRoutingRule()
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verify_module.verify(results=results)
