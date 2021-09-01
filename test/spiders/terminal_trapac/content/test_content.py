from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_terminal.trapac_share_spider import MainRoutingRule, CompanyInfo
from test.spiders.terminal_trapac import content


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=content, sample_path=sample_path)
    return sample_loader


def monkeypatch_container_response(monkeypatch, container_httptext):
    monkeypatch.setattr(
        MainRoutingRule, "_build_container_response", lambda *args, **kwargs: ("", container_httptext, {}),
    )


@pytest.mark.parametrize(
    "sub,container_no_list", [("01_only_container", "HDMU2596267,MAGU5764080,KKFU8087617,TRLU7333021,CAIU4444279"),],
)
def test_main_rule(sub, container_no_list, sample_loader, monkeypatch):
    # arrange
    container_httptext = sample_loader.read_file(sub, "container_sample.html")
    monkeypatch_container_response(monkeypatch=monkeypatch, container_httptext=container_httptext)
    rule = MainRoutingRule()
    option = MainRoutingRule.build_request_option(
        container_no_list=container_no_list.split(","),
        company_info=CompanyInfo(upper_short="LAX", lower_short="losangeles", email="", password=""),
    )
    response = TextResponse(url=option.url, request=Request(url=option.url, meta=option.meta,),)

    # action
    results = list(rule.handle(response=response))

    # assert
    verify_module = sample_loader.load_sample_module(sub, "verify")
    verify_module.verify(results=results)
