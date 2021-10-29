from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_carrier.rules import RuleManager
from crawler.spiders.carrier_rcl import MainInfoRoutingRule
from test.spiders.carrier_rcl import main_info


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=main_info, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    "sub,mbl_no,",
    [
        ("01_single_container", "NGBCB19030998"),
        ("02_multiple_container", "NGBCB19030160"),
        ("03_invalid_mbl_no", "NGBCB1903016"),
    ],
)
def test_main_info_routing_rule(sub, mbl_no, sample_loader):
    html_text = sample_loader.read_file(sub, "sample.html")

    option = MainInfoRoutingRule.build_request_option(mbl_no=mbl_no, form_data={}, endpoint="417Cargo_Tracking178")

    response = TextResponse(
        url=option.url,
        body=html_text,
        encoding="utf-8",
        request=Request(
            url=option.url,
            meta=option.meta,
        ),
    )

    routing_rule = MainInfoRoutingRule()
    results = list(routing_rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verify_module.verify(results=results)
