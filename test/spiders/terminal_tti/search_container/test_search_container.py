from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_terminal.items import InvalidContainerNoItem
from crawler.core_terminal.tti_wut_share_spider import MainRoutingRule
from test.spiders.terminal_tti import search_container
from crawler.spiders.terminal_tti import TerminalTtiSpider


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=search_container, sample_path=sample_path)
    return sample_loader


def monkeypatch_container_response(monkeypatch, httptext):
    monkeypatch.setattr(MainRoutingRule, "_build_container_response", lambda *args, **kwargs: httptext)


@pytest.mark.parametrize(
    "sub, container_no",
    [
        ("01_no_lfd", "FFAU1577392"),
        ("02_with_lfd", "CAIU4399890"),
    ],
)
def test_main_handle(sub, container_no, sample_loader, monkeypatch):
    httptext = sample_loader.read_file(sub, "sample.html")
    monkeypatch_container_response(monkeypatch=monkeypatch, httptext=httptext)

    option = MainRoutingRule.build_request_option(
        container_no_list=[container_no],
        company_info=TerminalTtiSpider.company_info,
    )
    response = TextResponse(
        url=option.url,
        encoding="utf-8",
        request=Request(
            url=option.url,
            meta=option.meta,
        ),
    )

    rule = MainRoutingRule()
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verify_module.verify(results=results)


@pytest.mark.skip
@pytest.mark.parametrize(
    "sub, container_no, invalid_no_item",
    [
        ("e01_invalid_container_no", "MSDU732250", InvalidContainerNoItem),
    ],
)
def test_invalid_container_no(sub, container_no, invalid_no_item, sample_loader, monkeypatch):
    httptext = sample_loader.read_file(sub, "sample.html")
    monkeypatch_container_response(monkeypatch=monkeypatch, httptext=httptext)

    option = MainRoutingRule.build_request_option(
        container_no_list=[container_no],
        company_info=TerminalTtiSpider.company_info,
    )
    response = TextResponse(
        url=option.url,
        encoding="utf-8",
        request=Request(
            url=option.url,
            meta=option.meta,
        ),
    )

    rule = MainRoutingRule()
    assert list(rule.handle(response=response)) == [invalid_no_item(container_no=container_no)]
