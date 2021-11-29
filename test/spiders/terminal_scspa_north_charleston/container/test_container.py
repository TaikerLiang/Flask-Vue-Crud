from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_terminal.scspa_share_spider import ContainerRoutingRule, ContentGetter
from test.spiders.terminal_scspa_north_charleston import container


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=container, sample_path=sample_path)
    return sample_loader


@pytest.mark.skip
@pytest.mark.parametrize(
    "sub,container_no",
    [
        ("01_basic", "EGHU8252850"),
    ],
)
def test_container(sub, container_no, sample_loader):
    httptext = sample_loader.read_file(sub, "sample.html")

    option = ContainerRoutingRule.build_request_option(container_nos=[container_no])

    response = TextResponse(
        url=option.url,
        body=httptext,
        encoding="utf-8",
        request=Request(
            url=option.url,
            meta={
                "container_nos": [container_no],
            },
        ),
    )

    rule = ContainerRoutingRule()
    results = list(rule._handle_response(response=response))

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verify_module.verify(results=results)
