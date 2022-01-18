from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_terminal.items import InvalidContainerNoItem
from crawler.core_terminal.tti_wut_share_spider import MainRoutingRule
from test.spiders.terminal_z952 import search_container
from crawler.spiders.terminal_z952 import TerminalTtiSpider


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=search_container, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    "sub, container_no",
    [
        ("01_no_lfd", "FFAU1577392"),
        ("02_with_lfd", "CAIU4399890"),
    ],
)
def test_main_handle(sub, container_no, sample_loader):
    httptext = sample_loader.read_file(sub, "sample.html")

    option = MainRoutingRule.build_request_option(
        container_no_list=[container_no],
        company_info=TerminalTtiSpider.company_info,
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

    results = list(MainRoutingRule._handle_response(response=response, container_no_list=[container_no]))

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verify_module.verify(results=results)


@pytest.mark.skip
@pytest.mark.parametrize(
    "sub, container_no, invalid_no_item",
    [
        ("e01_invalid_container_no", "MSDU732250", InvalidContainerNoItem),
    ],
)
def test_invalid_container_no(sub, container_no, invalid_no_item, sample_loader):
    httptext = sample_loader.read_file(sub, "sample.html")

    option = MainRoutingRule.build_request_option(
        container_no_list=[container_no],
        company_info=TerminalTtiSpider.company_info,
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

    assert list(MainRoutingRule._handle_response(response=response, container_no_list=[container_no])) == [
        invalid_no_item(container_no=container_no)
    ]
