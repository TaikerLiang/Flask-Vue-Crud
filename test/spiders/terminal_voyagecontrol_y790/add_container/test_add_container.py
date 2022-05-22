from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import HtmlResponse

from crawler.core_terminal.base import TERMINAL_RESULT_STATUS_ERROR
from crawler.core_terminal.items import ExportErrorData
from crawler.core_terminal.voyagecontrol_share_spider import AddContainerToTraceRoutingRule
from crawler.spiders.terminal_voyagecontrol_y790 import TerminalYtiSpider
from test.spiders.terminal_voyagecontrol_y790 import add_container


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=add_container, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    "sub,container_no",
    [
        ("01_valid_container", "CAIU7086501"),
    ],
)
def test_add_container_handle(sub, container_no, sample_loader):
    option = AddContainerToTraceRoutingRule.build_request_option(
        container_nos=[container_no],
        authorization_token="",
        company_info=TerminalYtiSpider.company_info,
    )

    response = HtmlResponse(
        status=200,
        url=option.url,
        body="",
        encoding="utf-8",
        request=Request(
            url=option.url,
            meta=option.meta,
        ),
    )

    rule = AddContainerToTraceRoutingRule()
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verify_module.verify(results=results)


@pytest.mark.skip
@pytest.mark.parametrize(
    "sub,container_no,status_code",
    [
        ("e01_invalid_container", "CMAU5610314", 502),
    ],
)
def test_add_container_handle_error(sub, container_no, status_code):
    expect_data_list = [
        ExportErrorData(
            container_no=container_no,
            detail="Data was not found",
            status=TERMINAL_RESULT_STATUS_ERROR,
        ),
    ]

    option = AddContainerToTraceRoutingRule.build_request_option(
        container_nos=[container_no],
        authorization_token="",
        company_info=TerminalYtiSpider.company_info,
    )

    response = HtmlResponse(
        status=status_code,
        url=option.url,
        body="",
        encoding="utf-8",
        request=Request(
            url=option.url,
            meta=option.meta,
        ),
    )

    rule = AddContainerToTraceRoutingRule()
    assert list(rule.handle(response=response)) == expect_data_list
