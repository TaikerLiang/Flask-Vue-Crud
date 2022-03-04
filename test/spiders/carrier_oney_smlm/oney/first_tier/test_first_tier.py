from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core.base import SEARCH_TYPE_MBL
from crawler.core_carrier.oney_smlm_share_spider import FirstTierRoutingRule
from crawler.spiders.carrier_oney import CarrierOneySpider
from test.spiders.carrier_oney_smlm.oney import first_tier


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=first_tier, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    "sub,mbl_no,base_url",
    [
        ("01_single_container", "SH9FSK690300", CarrierOneySpider.base_url),
        ("02_multiple_containers", "SZPVF2740514", CarrierOneySpider.base_url),
        ("03_data_not_found", "DALA35925000", CarrierOneySpider.base_url),
    ],
)
def test_first_tier_handle(sub, mbl_no, base_url, sample_loader):
    jsontext = sample_loader.read_file(sub, "sample.json")

    option = FirstTierRoutingRule.build_request_option(search_no=mbl_no, base_url=base_url, task_id="1")

    response = TextResponse(
        url=option.url,
        body=jsontext,
        encoding="utf-8",
        request=Request(
            url=option.url,
            meta=option.meta,
        ),
    )

    rule = FirstTierRoutingRule(search_type=SEARCH_TYPE_MBL)
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verify_module.verify(results=results)
