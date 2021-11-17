from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_carrier.base import SHIPMENT_TYPE_MBL
from crawler.core_carrier.exceptions import CarrierInvalidMblNoError, CarrierInvalidSearchNoError
from crawler.spiders.carrier_anlc_aplu_cmdu import FirstTierRoutingRule, CarrierCmduSpider
from crawler.core_carrier.anlc_aplu_cmdu_share_spider import FirstTierRoutingRule as MultiFirstTierRoutingRule
from crawler.spiders.carrier_cmdu_multi import CarrierCmduSpider as MultiCarrierCmduSpider
from test.spiders.carrier_cmdu import first_tier


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=first_tier, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    "sub,mbl_no",
    [
        ("01_not_finish", "CNPC001499"),
        ("02_finish", "NBSF300899"),
        ("03_multiple_containers", "NBSF301194"),
        ("04_por", "GGZ1004320"),
        ("05_dest", "NBSF301068"),
        ("06_data_not_found", "ATLHKN2119001"),
    ],
)
def test_first_tier_routing_rule(sample_loader, sub, mbl_no):
    html_text = sample_loader.read_file(sub, "main_info.html")

    option = FirstTierRoutingRule.build_request_option(
        search_no=mbl_no, search_type=SHIPMENT_TYPE_MBL, base_url=CarrierCmduSpider.base_url
    )

    response = TextResponse(
        url=option.url,
        encoding="utf-8",
        body=html_text,
        request=Request(
            url=option.url,
            meta=option.meta,
        ),
    )

    routing_rule = FirstTierRoutingRule(search_type=SHIPMENT_TYPE_MBL)
    results = list(routing_rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verify_module.verify(results=results)


@pytest.mark.parametrize(
    "sub,mbl_no",
    [
        ("01_not_finish", "CNPC001499"),
        ("02_finish", "NBSF300899"),
        ("03_multiple_containers", "NBSF301194"),
        ("04_por", "GGZ1004320"),
        ("05_dest", "NBSF301068"),
        ("06_data_not_found", "ATLHKN2119001"),
    ],
)
def test_multi_first_tier_routing_rule(sample_loader, sub, mbl_no):
    html_text = sample_loader.read_file(sub, "main_info.html")

    option = MultiFirstTierRoutingRule.build_request_option(
        search_nos=[mbl_no], task_ids=[1], search_type=SHIPMENT_TYPE_MBL, base_url=MultiCarrierCmduSpider.base_url
    )

    response = TextResponse(
        url=option.url,
        encoding="utf-8",
        body=html_text,
        request=Request(
            url=option.url,
            meta=option.meta,
        ),
    )

    routing_rule = MultiFirstTierRoutingRule(search_type=SHIPMENT_TYPE_MBL)
    results = list(routing_rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verify_module.multi_verify(results=results)
