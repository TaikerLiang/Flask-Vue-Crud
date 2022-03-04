from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core.base import SEARCH_TYPE_MBL
from crawler.core_carrier.oney_smlm_share_spider import ReleaseStatusRoutingRule
from crawler.spiders.carrier_smlm import CarrierSmlmSpider
from test.spiders.carrier_oney_smlm.smlm import release_status


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=release_status, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    "sub,mbl_no,cntr_no,bkg_no",
    [
        ("01", "SHSM9C747300", "CCLU3451951", "SHSM9C747300"),
    ],
)
def test_release_status_handle(sub, mbl_no, cntr_no, bkg_no, sample_loader):
    jsontext = sample_loader.read_file(sub, "sample.json")

    option = ReleaseStatusRoutingRule.build_request_option(
        container_no=cntr_no,
        booking_no=bkg_no,
        base_url=CarrierSmlmSpider.base_url,
        task_id="1",
        search_type=SEARCH_TYPE_MBL,
        search_no=bkg_no,
    )

    response = TextResponse(
        url=option.url,
        body=jsontext,
        encoding="utf-8",
        request=Request(
            url=option.url,
            meta=option.meta,
        ),
    )

    rule = ReleaseStatusRoutingRule()
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verify_module.verify(results=results)
