from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.spiders.terminal_z165 import ContainerRoutingRule
from test.spiders.terminal_z165 import container


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=container, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    "sub,container_no",
    [
        ("01_basic", "OTPU6344278"),
        ("02_no_last_free_date", "TWCU8058905"),
        ("03_data_not_found", "SEGU6853042"),
    ],
)
def test_container_handle(sub, container_no, sample_loader):
    http_text = sample_loader.read_file(sub, "sample.html")

    option = ContainerRoutingRule.build_request_option(container_no=container_no)

    response = TextResponse(
        url=option.url,
        body=http_text,
        encoding="utf-8",
        request=Request(
            url=option.url,
            meta={
                "container_no": container_no,
            },
        ),
    )

    rule = ContainerRoutingRule()
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verify_module.verify(results=results)
