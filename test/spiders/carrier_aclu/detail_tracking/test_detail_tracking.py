from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.spiders.carrier_aclu import DetailTrackingRoutingRule
from test.spiders.carrier_aclu import detail_tracking


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=detail_tracking, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    "sub,container_no",
    [
        ("01_basic", "ACLU9685173"),
    ],
)
def test_detail_tracking_info_routing_rule(sub, container_no, sample_loader):
    httptext = sample_loader.read_file(sub, "sample.json")
    option = DetailTrackingRoutingRule.build_request_option(route={}, request_data="", container_no=container_no)

    response = TextResponse(
        url=option.url,
        body=httptext,
        encoding="utf-8",
        request=Request(
            url=option.url,
        ),
    )

    routing_rule = DetailTrackingRoutingRule()
    results = list(routing_rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verify_module.verify(results=results)
