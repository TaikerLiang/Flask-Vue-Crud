from pathlib import Path

import pytest
from scrapy import Request, Selector
from scrapy.http import TextResponse

from crawler.core_terminal.exceptions import TerminalInvalidContainerNoError, TerminalInvalidMblNoError
from crawler.spiders.terminal_trapac import ContentRoutingRule, Location
from test.spiders.terminal_trapac import content


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=content, sample_path=sample_path)
    return sample_loader


def monkeypatch_container_response(monkeypatch, container_httptext):
    monkeypatch.setattr(
        ContentRoutingRule,
        '_build_container_response',
        lambda *args, **kwargs: Selector(text=container_httptext),
    )


def monkeypatch_mbl_response(monkeypatch, mbl_httptext):
    monkeypatch.setattr(
        ContentRoutingRule,
        '_build_mbl_response',
        lambda *args, **kwargs: Selector(text=mbl_httptext),
    )


@pytest.mark.parametrize(
    'sub,container_no,mbl_no',
    [
        ('01_only_container', 'YMMU4127027', ''),
        ('02_container_and_mbl', 'KOCU4427065', 'NXWB7009876'),
    ],
)
def test_content_routing_rule(sub, container_no, mbl_no, sample_loader, monkeypatch):
    container_httptext = sample_loader.read_file(sub, 'container_sample.html')
    mbl_httptext = sample_loader.read_file(sub, 'mbl_sample.html')

    monkeypatch_container_response(monkeypatch=monkeypatch, container_httptext=container_httptext)
    monkeypatch_mbl_response(monkeypatch=monkeypatch, mbl_httptext=mbl_httptext)

    rule = ContentRoutingRule()
    option = ContentRoutingRule.build_request_option(
        location=Location.LOS_ANGELES.value,
        container_no=container_no,
        mbl_no=mbl_no,
    )
    response = TextResponse(
        url=option.url,
        request=Request(
            url=option.url,
            meta=option.meta,
        ),
    )
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)


@pytest.mark.parametrize(
    'sub,container_no,mbl_no,expect_exception',
    [
        ('e01_invalid_container_no', 'KOCU442706', '', TerminalInvalidContainerNoError),
        ('e02_invalid_mbl_no', 'KOCU4427065', 'NXWB700987', TerminalInvalidMblNoError),
    ],
)
def test_content_search_no_invalid_error(sub, container_no, mbl_no, expect_exception, sample_loader, monkeypatch):
    container_httptext = sample_loader.read_file(sub, 'container_sample.html')
    mbl_httptext = sample_loader.read_file(sub, 'mbl_sample.html')

    monkeypatch_container_response(monkeypatch=monkeypatch, container_httptext=container_httptext)
    monkeypatch_mbl_response(monkeypatch=monkeypatch, mbl_httptext=mbl_httptext)

    option = ContentRoutingRule.build_request_option(
        location=Location.LOS_ANGELES.value,
        container_no=container_no,
        mbl_no=mbl_no,
    )
    response = TextResponse(
        url=option.url,
        request=Request(
            url=option.url,
            meta=option.meta,
        ),
    )

    rule = ContentRoutingRule()
    with pytest.raises(expect_exception):
        list(rule.handle(response=response))
