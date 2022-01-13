from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_terminal.items import InvalidContainerNoItem
from crawler.core_terminal.tti_wut_share_spider import MainRoutingRule
from test.spiders.terminal_z705 import search_container
from crawler.spiders.terminal_z705 import TerminalWutSpider


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=search_container, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    "sub, container_no",
    [
        ("01_no_lfd", "TGBU4645596"),
        ("02_with_lfd", "YMMU6297676"),
    ],
)
def test_search_container_handle(sub, container_no, sample_loader):
    httptext = sample_loader.read_file(sub, "sample.html")

    option = MainRoutingRule.build_request_option(
        container_no_list=[container_no],
        company_info=TerminalWutSpider.company_info,
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
def test_search_container_handle_error(sub, container_no, invalid_no_item, sample_loader):
    httptext = sample_loader.read_file(sub, "sample.html")

    option = MainRoutingRule.build_request_option(
        container_no_list=[container_no],
        company_info=TerminalWutSpider.company_info,
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
