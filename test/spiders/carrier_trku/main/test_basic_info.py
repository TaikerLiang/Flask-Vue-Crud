from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core.base_new import SEARCH_TYPE_MBL
from crawler.spiders.carrier_trku import HiddenFormSpec, MainRoutingRule
from test.spiders.carrier_trku import main


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=main, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    "sub,mbl_no",
    [
        ("01_basic", "TRKU10023023"),
        ("02_data_not_found", "TRKU10000000"),
    ],
)
def test_main_info_routing_rule(sub, mbl_no, sample_loader):
    json_text = sample_loader.read_file(sub, "sample.html")

    hidden_form_spec = HiddenFormSpec(
        view_state="",
        view_state_generator="",
    )

    option = MainRoutingRule.build_request_option(
        search_nos=[mbl_no], task_ids=["1"], hidden_form_spec=hidden_form_spec
    )

    response = TextResponse(
        url=option.url,
        body=json_text,
        encoding="utf-8",
        request=Request(
            url=option.url,
            meta=option.meta,
        ),
    )

    routing_rule = MainRoutingRule(search_type=SEARCH_TYPE_MBL)
    results = list(routing_rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verify_module.verify(results=results)
