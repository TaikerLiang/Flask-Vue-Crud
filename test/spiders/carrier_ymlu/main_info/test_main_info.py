from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.spiders.carrier_ymlu import HiddenFormSpec, MainInfoRoutingRule
from test.spiders.carrier_ymlu import main_info


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=main_info, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    "sub,mbl_no,",
    [
        ("01_all_exist", "W216104890"),
        ("02_no_xta", "W209047989"),
        ("03_no_release", "I209365239"),
        ("04_multi_containers", "W241061370"),
        ("05_with_firm_code", "W226020752"),
        ("05_with_empty_firm_code", "I209431722"),
        ("06_ip_blocked", "E209048375"),
        ("07_delivery_without_time_status", "W209139591"),
        ("08_to_be_advised_ver2", "W470030608"),
        ("09_invalid_mbl_no", "I209383517"),
    ],
)
def test_main_info_routing_rule(sub, mbl_no, sample_loader):
    httptext = sample_loader.read_file(sub, "sample.html")

    request_option = MainInfoRoutingRule.build_request_option(
        mbl_no=mbl_no,
        hidden_form_spec=HiddenFormSpec(view_state_generator="", view_state="", event_validation="", previous_page=""),
        captcha="",
        headers={},
    )

    response = TextResponse(
        url=request_option.url,
        body=httptext,
        encoding="utf-8",
        request=Request(
            url=request_option.url,
            meta=request_option.meta,
        ),
    )

    rule = MainInfoRoutingRule()
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verify_module.verify(results=results)
