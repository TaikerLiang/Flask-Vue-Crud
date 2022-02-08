from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_terminal.base import TERMINAL_RESULT_STATUS_ERROR
from crawler.core_terminal.items import ExportErrorData
from crawler.core_terminal.trapac_share_spider import MainRoutingRule
from crawler.spiders.terminal_trapac_y549 import TerminalTrapacOakSpider
from test.spiders.terminal_trapac_y549 import main


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=main, sample_path=sample_path)
    return sample_loader


@pytest.mark.skip
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
        container_no_list=[container_no],
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
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verify_module.verify(results=results)


@pytest.mark.skip
@pytest.mark.parametrize(
    "sub,container_no",
    [
        ("e01_invalid_container_no", "KOCU442706"),
    ],
)
def test_invalid_container_no(sub, container_no, sample_loader):
    expect_data_list = [
        ExportErrorData(
            container_no=container_no,
            detail="Data was not found",
            status=TERMINAL_RESULT_STATUS_ERROR,
        ),
    ]

    html_text = sample_loader.read_file(sub, "sample.html")

    option = MainRoutingRule.build_request_option(
        container_no_list=[container_no],
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
    assert list(rule.handle(response=response)) == expect_data_list
