from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core.items import ExportErrorData
from crawler.core_terminal.exceptions import TERMINAL_RESULT_STATUS_ERROR
from crawler.core_terminal.stg_share_spider import (
    SHIPMENT_TYPE_CONTAINER,
    ContainerRoutingRule,
)
from test.spiders.terminal_stg_y292 import container


@pytest.mark.skip()
@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=container, sample_path=sample_path)
    return sample_loader


@pytest.mark.skip()
@pytest.mark.parametrize(
    "sub,container_no",
    [
        ("01_basic", "OOLU9879270"),
        ("02_multi_containers", "OOLU6258622"),
    ],
)
def test_container_handle(sub, container_no, sample_loader):
    http_text = sample_loader.read_file(sub, "sample.html")

    option = ContainerRoutingRule.build_request_option(search_no=container_no, search_type=SHIPMENT_TYPE_CONTAINER)

    response = TextResponse(
        url=option.url,
        body=http_text,
        encoding="utf-8",
        request=Request(
            url=option.url,
            meta=option.meta,
        ),
    )

    rule = ContainerRoutingRule()
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verify_module.verify(results=results)


@pytest.mark.skip()
@pytest.mark.parametrize(
    "sub,container_no",
    [
        ("e01_data_not_found", "EISU3920168"),
    ],
)
def test_data_not_found(sub, container_no, sample_loader):
    expected_data_list = [
        ExportErrorData(
            container_no=container_no,
            status=TERMINAL_RESULT_STATUS_ERROR,
            detail="Data was not found",
        )
    ]

    http_text = sample_loader.read_file(sub, "sample.html")

    option = ContainerRoutingRule.build_request_option(search_no=container_no, search_type=SHIPMENT_TYPE_CONTAINER)

    response = TextResponse(
        url=option.url,
        body=http_text,
        encoding="utf-8",
        request=Request(
            url=option.url,
            meta=option.meta,
        ),
    )

    rule = ContainerRoutingRule()
    assert list(rule.handle(response=response)) == expected_data_list
