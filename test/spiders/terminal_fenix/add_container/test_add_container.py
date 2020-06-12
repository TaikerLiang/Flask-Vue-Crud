from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import HtmlResponse

from crawler.core_terminal.exceptions import TerminalInvalidContainerNoError
from crawler.spiders.terminal_fenix import LoginRoutingRule, AddContainerToTraceRoutingRule
from test.spiders.terminal_fenix import add_container


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=add_container, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,container_no', [
    ('01_valid_container', 'CAIU7086501'),
])
def test_add_container_handle(sub, container_no, sample_loader):
    option = AddContainerToTraceRoutingRule.build_request_option(
        container_no=container_no, authorization_token=''
    )

    response = HtmlResponse(
        status=200,
        url=option.url,
        body='',
        encoding='utf-8',
        request=Request(
            url=option.url,
            meta=option.meta,
        ),
    )

    rule = AddContainerToTraceRoutingRule()
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)


@pytest.mark.parametrize('sub,container_no,status_code,expect_exception', [
    ('01_invalid_container', 'CMAU5610314', 502, TerminalInvalidContainerNoError),
])
def test_add_container_handle_error(sub, container_no, status_code, expect_exception, sample_loader):
    option = AddContainerToTraceRoutingRule.build_request_option(
        container_no=container_no, authorization_token=''
    )

    response = HtmlResponse(
        status=status_code,
        url=option.url,
        body='',
        encoding='utf-8',
        request=Request(
            url=option.url,
            meta=option.meta,
        ),
    )

    rule = AddContainerToTraceRoutingRule()
    with pytest.raises(expect_exception):
        list(rule.handle(response=response))

