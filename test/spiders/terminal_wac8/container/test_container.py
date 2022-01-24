from pathlib import Path
from crawler.core_terminal.items import InvalidContainerNoItem

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.spiders.terminal_wac8 import ContainerRoutingRule
from test.spiders.terminal_wac8 import container


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=container, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    "sub, container_no",
    [
        ("01_basic", "TCNU3577497"),
        ("02_available", "WHLU0343058"),
    ],
)
def test_container_handle(sub, container_no, sample_loader):
    json_text = sample_loader.read_file(sub, "sample.json")

    option = ContainerRoutingRule.build_request_option(container_no_list=[container_no])

    response = TextResponse(
        url=option.url,
        body=json_text,
        encoding="utf-8",
        request=Request(
            url=option.url,
            meta=option.meta,
        ),
    )

    rule = ContainerRoutingRule()
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verify_module.verify(results=results)


@pytest.mark.skip
@pytest.mark.parametrize(
    "sub, container_no, invalid_no_item",
    [
        ("e01_invalid_container_no", "WHLU7414414", InvalidContainerNoItem),
    ],
)
def test_container_handle(sub, container_no, invalid_no_item, sample_loader):
    json_text = sample_loader.read_file(sub, "sample.json")

    option = ContainerRoutingRule.build_request_option(container_no_list=[container_no])

    response = TextResponse(
        url=option.url,
        body=json_text,
        encoding="utf-8",
        request=Request(
            url=option.url,
            meta=option.meta,
        ),
    )

    rule = ContainerRoutingRule()
    assert list(rule.handle(response=response)) == [invalid_no_item(container_no=container_no)]