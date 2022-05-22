from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.spiders.carrier_eglv import ReleaseStatusRoutingRule
from test.spiders.carrier_eglv import release_status


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=release_status, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    "sub,mbl_no,",
    [
        ("01_all_fill", "143982920890"),
        ("02_release_status_data_not_found", "003902773938"),
    ],
)
def test_release_status_handler(sub, mbl_no, sample_loader):
    httptext = sample_loader.read_file(sub, "sample.html")

    option = ReleaseStatusRoutingRule.build_request_option(
        search_no=mbl_no,
    )

    response = TextResponse(
        url=option.url,
        body=httptext,
        encoding="utf-8",
        request=Request(
            url=option.url,
        ),
    )

    rule = ReleaseStatusRoutingRule()
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verifier = verify_module.Verifier()
    verifier.verify(results=results)
