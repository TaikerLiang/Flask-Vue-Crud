from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_terminal.items import InvalidContainerNoItem
from crawler.core_terminal.portsamerica_share_spider import SearchContainerRule
from crawler.spiders.terminal_wbct import TerminalWbctSpider
from test.spiders.terminal_wbct import search_container


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=search_container, sample_path=sample_path)
    return sample_loader


def monkeypatch_container_response(monkeypatch, httptext):
    monkeypatch.setattr(SearchContainerRule, "_build_container_response", lambda *args, **kwargs: httptext)


@pytest.mark.parametrize(
    "sub, container_no",
    [
        ("01_basic", "ZCSU8739851"),
        ("02_available", "CCLU7014409"),
    ],
)
def test_container_handle(sub, container_no, sample_loader, monkeypatch):
    httptext = sample_loader.read_file(sub, "sample.html")
    monkeypatch_container_response(monkeypatch=monkeypatch, httptext=httptext)

    option = SearchContainerRule.build_request_option(
        container_no_list=[container_no], company_info=TerminalWbctSpider.company_info
    )

    response = TextResponse(
        url=option.url,
        encoding="utf-8",
        request=Request(
            url=option.url,
            meta=option.meta,
        ),
    )

    rule = SearchContainerRule()
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verify_module.verify(results=results)


@pytest.mark.skip
@pytest.mark.parametrize(
    "sub,container_no,invalid_no_item",
    [
        ("e01_invalid_container_no", "CCLU7014414", InvalidContainerNoItem),
    ],
)
def test_invalid_container_no(sub, container_no, invalid_no_item, sample_loader, monkeypatch):
    httptext = sample_loader.read_file(sub, "sample.html")
    monkeypatch_container_response(monkeypatch=monkeypatch, httptext=httptext)

    request_option = SearchContainerRule.build_request_option(
        container_no_list=[container_no], company_info=TerminalWbctSpider.company_info
    )

    response = TextResponse(
        url=request_option.url,
        encoding="utf-8",
        request=Request(
            url=request_option.url,
            meta=request_option.meta,
        ),
    )

    rule = SearchContainerRule()
    assert list(rule.handle(response=response)) == [invalid_no_item(container_no=container_no)]
