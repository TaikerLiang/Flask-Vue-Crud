from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_terminal.base import TERMINAL_RESULT_STATUS_ERROR
from crawler.core_terminal.items import ExportErrorData
from crawler.spiders.terminal_y178 import ContainerRoutingRule
from test.spiders.terminal_y178 import container


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=container, sample_path=sample_path)
    return sample_loader


@pytest.mark.skip  # skip due to website failure
@pytest.mark.parametrize(
    "sub,container_no,",
    [
        ("01_basic", "KKFU7634200"),
    ],
)
def test_container_routing_rule(sub, container_no, sample_loader):
    httptext = sample_loader.read_file(sub, "sample.html")

    request_option = ContainerRoutingRule.build_request_option(container_no_list=[container_no])

    response = TextResponse(
        url=request_option.url,
        body=httptext,
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


@pytest.mark.skip
@pytest.mark.parametrize(
    "sub,container_no",
    [
        ("e01_invalid_container_no", "TGBU678745"),
    ],
)
def test_invalid_container_no(sub, container_no, sample_loader):
    expect_data_list = [
        ExportErrorData(
            container_no=container_no,
            detail="Data was not found",
            status=TERMINAL_RESULT_STATUS_ERROR,
        ),
    ]

    httptext = sample_loader.read_file(sub, "sample.html")

    request_option = ContainerRoutingRule.build_request_option(container_no_list=[container_no])

    response = TextResponse(
        url=request_option.url,
        body=httptext,
        encoding="utf-8",
        request=Request(
            url=request_option.url,
            meta=request_option.meta,
        ),
    )

    rule = ContainerRoutingRule()
    assert list(rule.handle(response=response)) == expect_data_list
