from pathlib import Path
from test.spiders.carrier_aplu import search

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_carrier.anlc_aplu_cmdu_share_spider import (
    SearchRoutingRule as MultiSearchRoutingRule,
)
from crawler.core_carrier.base import SHIPMENT_TYPE_MBL
from crawler.spiders.carrier_anlc_aplu_cmdu import CarrierApluSpider, SearchRoutingRule
from crawler.spiders.carrier_aplu_multi import (
    CarrierApluSpider as MultiCarrierApluSpider,
)


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=search, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    "sub,mbl_no",
    [
        ("01_not_finish", "NBSN916951"),
        ("02_finish", "USG0193096"),
        ("03_por", "TWN0638760"),
        ("04_dest", "SHZ4558031"),
        ("05_data_not_found", "ATLHKN2119001"),
    ],
)
def test_search_routing_rule(sample_loader, sub, mbl_no):
    html_text = sample_loader.read_file(sub, "main_info.html")

    option = SearchRoutingRule.build_request_option(
        search_no=mbl_no,
        search_type=SHIPMENT_TYPE_MBL,
        base_url=CarrierApluSpider.base_url,
        g_recaptcha_res="",
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

    routing_rule = SearchRoutingRule()
    results = list(routing_rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verify_module.verify(results=results)


@pytest.mark.parametrize(
    "sub,mbl_no",
    [
        ("01_not_finish", "SGN1408239"),
        ("02_finish", "NBSF300899"),
        ("03_por", "CSI0144188"),
        ("04_dest", "NBSN922368A"),
        ("05_data_not_found", "ATLHKN2119001"),
    ],
)
def test_multi_search_routing_rule(sample_loader, sub, mbl_no):
    html_text = sample_loader.read_file(sub, "main_info.html")

    option = MultiSearchRoutingRule.build_request_option(
        search_nos=[mbl_no],
        task_ids=[1],
        search_type=SHIPMENT_TYPE_MBL,
        base_url=MultiCarrierApluSpider.base_url,
        g_recaptcha_res="",
        research_times=0,
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

    routing_rule = MultiSearchRoutingRule()
    results = list(routing_rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verify_module.multi_verify(results=results)
