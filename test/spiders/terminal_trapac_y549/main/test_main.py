from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core.base import RESULT_STATUS_ERROR, SEARCH_TYPE_CONTAINER
from crawler.core.items import DataNotFoundItem
from crawler.core_terminal.trapac_share_spider import MainRoutingRule
from crawler.spiders.terminal_trapac_y549 import TerminalTrapacOakSpider
from test.spiders.terminal_trapac_y549 import main


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=main, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    "sub,container_no",
    [
        ("01_basic", "HLBU2708375"),
        ("02_no_holds", "TTNU8130668"),
    ],
)
def test_main_routing_rule(sub, container_no, sample_loader):
    html_text = sample_loader.read_file(sub, "sample.html")

    option = MainRoutingRule.build_request_option(
        container_nos=[container_no],
        cno_tid_map={container_no: ["1"]},
        company_info=TerminalTrapacOakSpider.company_info,
    )
    response = TextResponse(
        url=option.url,
        body=html_text,
        encoding="utf-8",
        request=Request(
            url=option.url,
            meta=option.meta,
        ),
    )
    rule = MainRoutingRule()
    results = list(rule.handle_response(response=response.text, container_nos=[container_no]))

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verify_module.verify(results=results)


@pytest.mark.parametrize(
    "sub,container_no",
    [
        ("e01_invalid_container_no", "KOCU442706"),
    ],
)
def test_invalid_container_no(sub, container_no, sample_loader):
    expect_data = DataNotFoundItem(
        search_no=container_no,
        search_type=SEARCH_TYPE_CONTAINER,
        detail="Data was not found",
        status=RESULT_STATUS_ERROR,
    )

    html_text = sample_loader.read_file(sub, "sample.html")

    option = MainRoutingRule.build_request_option(
        container_nos=[container_no],
        cno_tid_map={container_no: ["1"]},
        company_info=TerminalTrapacOakSpider.company_info,
    )
    response = TextResponse(
        url=option.url,
        body=html_text,
        encoding="utf-8",
        request=Request(
            url=option.url,
            meta=option.meta,
        ),
    )

    rule = MainRoutingRule()
    assert list(rule.handle_response(response=response.text, container_nos=[container_no]))[-1] == expect_data
