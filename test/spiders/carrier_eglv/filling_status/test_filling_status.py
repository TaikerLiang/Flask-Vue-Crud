from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.spiders.carrier_eglv import FilingStatusRoutingRule
from test.spiders.carrier_eglv import filling_status


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=filling_status, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    "sub,mbl_no,",
    [
        ("01_only_us", "003902245109"),
        ("02_ca_and_us", "143986250473"),
        ("03_without_us", "149905244604"),
    ],
)
def test_filing_status_handler(sub, mbl_no, sample_loader):
    httptext = sample_loader.read_file(sub, "sample.html")

    option = FilingStatusRoutingRule.build_request_option(
        search_no=mbl_no,
        first_container_no="",
        pod="",
    )

    response = TextResponse(
        url=option.url,
        body=httptext,
        encoding="utf-8",
        request=Request(
            url=option.url,
            meta=option.meta,
        ),
    )

    rule = FilingStatusRoutingRule()
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verifier = verify_module.Verifier()
    verifier.verify(results=results)
