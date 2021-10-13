from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_terminal.exceptions import TerminalInvalidContainerNoError
from crawler.spiders.terminal_newyork_container import ContainerRoutingRule
from test.spiders.terminal_newyork_container import container


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=container, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    "sub, container_no_list",
    [
        ("01_basic", ["TCLU7732296", "SEGU4568364", "YMMU1023477"]),
    ],
)
def test_container_handle(sub, container_no_list, sample_loader):
    httptext = sample_loader.read_file(sub, "sample.json")

    option = ContainerRoutingRule.build_request_option(
        container_no_list=container_no_list,
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
    "sub, container_no, expect_exception",
    [
        ("e01_invalid_container_no", "TCLK7732297", TerminalInvalidContainerNoError),
    ],
)
def test_invalid_container_no(sub, container_no, expect_exception, sample_loader):
    httptext = sample_loader.read_file(sub, "sample.json")

    option = ContainerRoutingRule.build_request_option(
        container_no_list=[container_no],
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
    with pytest.raises(expect_exception):
        list(rule.handle(response=response))
