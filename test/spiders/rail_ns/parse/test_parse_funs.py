from pathlib import Path

import pytest
from scrapy import Request, Selector
from scrapy.http import TextResponse

from crawler.spiders.rail_ns import ContainerRoutingRule, TrackAndTraceTableLocator
from test.spiders.rail_ns import parse


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=parse, sample_path=sample_path)
    return sample_loader


@pytest.mark.skip
@pytest.mark.parametrize(
    "sub,container_no",
    [
        ("01_basic", "GLDU9672840"),
    ],
)
def test_track_and_trace_table_locator(sub, container_no, sample_loader):
    html_text = sample_loader.read_file(sub, "sample.html")

    option = ContainerRoutingRule.build_request_option(container_nos=[container_no], proxy_manager=None)

    response = TextResponse(
        url=option.url,
        body=html_text,
        encoding="utf-8",
        request=Request(
            url=option.url,
            meta=option.meta,
        ),
    )

    table_locator = TrackAndTraceTableLocator()
    table_locator.parse(table=Selector(response))
