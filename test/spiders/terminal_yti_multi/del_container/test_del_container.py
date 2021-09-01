from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import HtmlResponse

from crawler.core_terminal.exceptions import TerminalInvalidContainerNoError
from crawler.spiders.terminal_fenix import AddContainerToTraceRoutingRule, DelContainerFromTraceRoutingRule
from test.spiders.terminal_yti_multi import del_container


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=del_container, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    'sub,container_no,not_finished',
    [('01_del_for_update', 'CAIU7086501', True), ('02_del_after_search', 'CMAU6382395', False)],
)
def test_del_container_handle(sub, container_no, not_finished, sample_loader):
    option = DelContainerFromTraceRoutingRule.build_request_option(
        container_no=container_no, authorization_token='', not_finished=not_finished
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

    rule = DelContainerFromTraceRoutingRule()
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)
