from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_terminal.exceptions import TerminalInvalidContainerNoError
from crawler.spiders.terminal_tos import ContainerDetailRoutingRule
from test.spiders.terminal_tos import container_detail


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=container_detail, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    'sub,container_no,',
    [
        ('01_basic', 'TGBU6787455'),
    ],
)
def test_container_detail_routing_rule(sub, container_no, sample_loader):
    httptext = sample_loader.read_file(sub, 'sample.html')

    request_option = ContainerDetailRoutingRule.build_request_option(container_no=container_no)

    response = TextResponse(
        url=request_option.url,
        body=httptext,
        encoding='utf-8',
        request=Request(
            url=request_option.url,
        ),
    )

    rule = ContainerDetailRoutingRule()
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)


@pytest.mark.parametrize(
    'sub,container_no,expect_exception',
    [
        ('e01_invalid_container_no', 'TGBU6787', TerminalInvalidContainerNoError),
    ],
)
def test_container_detail_invalid_container_no_error(sub, container_no, expect_exception, sample_loader):
    httptext = sample_loader.read_file(sub, 'sample.html')

    request_option = ContainerDetailRoutingRule.build_request_option(container_no=container_no)

    response = TextResponse(
        url=request_option.url,
        body=httptext,
        encoding='utf-8',
        request=Request(
            url=request_option.url,
        ),
    )

    rule = ContainerDetailRoutingRule()
    with pytest.raises(expect_exception):
        list(rule.handle(response=response))
