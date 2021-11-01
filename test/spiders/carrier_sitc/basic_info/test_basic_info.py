from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_carrier.exceptions import CarrierInvalidMblNoError
from crawler.spiders.carrier_sitc import BasicInfoRoutingRule
from test.spiders.carrier_sitc import basic_info


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=basic_info, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    "sub,mbl_no", [("01_basic", "SITDSHSGZ02389"), ("02_data_not_found", "SITDSHSGZ02418"),],
)
def test_main_info_routing_rule(sub, mbl_no, sample_loader):
    json_text = sample_loader.read_file(sub, "sample.json")

    option = BasicInfoRoutingRule.build_request_option(mbl_no=mbl_no, rand_str="", captcha_code="")

    response = TextResponse(
        url=option.url, body=json_text, encoding="utf-8", request=Request(url=option.url, meta={"mbl_no": mbl_no,},),
    )

    routing_rule = BasicInfoRoutingRule()
    results = list(routing_rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verify_module.verify(results=results)
