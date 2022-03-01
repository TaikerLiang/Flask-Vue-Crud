from pathlib import Path
from test.spiders.carrier_anlc import search

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core.base import SEARCH_TYPE_CONTAINER, SEARCH_TYPE_MBL
from crawler.core_carrier.anlc_aplu_cmdu_share_spider import (
    SearchRoutingRule as MultiSearchRoutingRule,
)
from crawler.spiders.carrier_anlc_aplu_cmdu import CarrierAnlcSpider, SearchRoutingRule
from crawler.spiders.carrier_anlc_multi import (
    CarrierAnlcSpider as MultiCarrierAnlcSpider,
)


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=search, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    "sub,search_no,search_type",
    [
        ("01_not_finish", "AWT0167294", SEARCH_TYPE_MBL),
        ("02_finish", "CMAU0720010", SEARCH_TYPE_CONTAINER),
        ("03_por", "CSI0144188", SEARCH_TYPE_MBL),
        ("04_dest", "TCLU7703472", SEARCH_TYPE_CONTAINER),
        ("05_data_not_found", "ATLHKN2119001", SEARCH_TYPE_MBL),
    ],
)
def test_search_routing_rule(sample_loader, sub, search_no, search_type):
    html_text = sample_loader.read_file(sub, "main_info.html")

    option = SearchRoutingRule.build_request_option(
        task_id="1",
        search_no=search_no,
        search_type=search_type,
        base_url=CarrierAnlcSpider.base_url,
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
    "sub,search_no,search_type",
    [
        ("01_not_finish", "AWT0167294", SEARCH_TYPE_MBL),
        ("02_finish", "CMAU0720010", SEARCH_TYPE_CONTAINER),
        ("03_por", "CSI0144188", SEARCH_TYPE_MBL),
        ("04_dest", "TCLU7703472", SEARCH_TYPE_CONTAINER),
        ("05_data_not_found", "ATLHKN2119001", SEARCH_TYPE_MBL),
    ],
)
def test_multi_search_routing_rule(sample_loader, sub, search_no, search_type):
    html_text = sample_loader.read_file(sub, "main_info.html")

    option = MultiSearchRoutingRule.build_request_option(
        search_nos=[search_no],
        task_ids=["1"],
        search_type=search_type,
        base_url=MultiCarrierAnlcSpider.base_url,
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
