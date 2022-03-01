from pathlib import Path
from test.spiders.carrier_cmdu import search

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core.base import SEARCH_TYPE_MBL
from crawler.core_carrier.anlc_aplu_cmdu_share_spider import (
    SearchRoutingRule as MultiSearchRoutingRule,
)
from crawler.spiders.carrier_anlc_aplu_cmdu import CarrierCmduSpider, SearchRoutingRule
from crawler.spiders.carrier_cmdu_multi import (
    CarrierCmduSpider as MultiCarrierCmduSpider,
)


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=search, sample_path=sample_path)
    return sample_loader


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
def test_search_routing_rule(sample_loader, sub, mbl_no):
    html_text = sample_loader.read_file(sub, "main_info.html")

    option = SearchRoutingRule.build_request_option(
        task_id="1",
        search_no=mbl_no,
        search_type=SEARCH_TYPE_MBL,
        base_url=CarrierCmduSpider.base_url,
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
        task_ids=["1"],
        search_type=SEARCH_TYPE_MBL,
        base_url=MultiCarrierCmduSpider.base_url,
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
