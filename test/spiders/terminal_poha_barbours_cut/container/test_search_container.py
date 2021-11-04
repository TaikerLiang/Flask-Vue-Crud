from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_terminal.poha_share_spider import ContainerRoutingRule
from test.spiders.terminal_poha_barbours_cut import container


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=container, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    "sub, container_no",
    [
        ("01_basic", "EITU1692078"),
    ],
)
def test_container_handle(sub, container_no, sample_loader):
    httptext = sample_loader.read_file(sub, "sample.html")

    option = ContainerRoutingRule.build_request_option(
        task_id=1,
        container_no=container_no,
        cookies={},
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
    rule = ContainerRoutingRule()
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verify_module.verify(results=results)


@pytest.mark.parametrize(
    "sub, container_no",
    [
        ("e01_invalid_container_no", "QQQQQQQQQQQ"),
    ],
)
def test_invalid_container_no(sub, container_no, sample_loader):
    httptext = sample_loader.read_file(sub, "sample.html")

    option = ContainerRoutingRule.build_request_option(
        task_id=1,
        container_no=container_no,
        cookies={},
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
    rule = ContainerRoutingRule()
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verify_module.verify(results=results)


@pytest.mark.parametrize(
    "sub, container_no",
    [
        ("e02_container_no_not_meet", "EITU1692078"),
    ],
)
def test_container_no_not_meet(sub, container_no, sample_loader):
    httptext = sample_loader.read_file(sub, "sample.html")

    option = ContainerRoutingRule.build_request_option(
        task_id=1,
        container_no=container_no,
        cookies={},
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
    rule = ContainerRoutingRule()
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verify_module.verify(results=results)
