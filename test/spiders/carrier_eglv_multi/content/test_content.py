from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.spiders.carrier_eglv_multi import CargoTrackingRoutingRule
from test.spiders.carrier_eglv_multi import content


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=content, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    "sub,mbl_no,",
    [
        ("01_invalid_mbl_no", "003901796617"),
        ("02_invalid_mbl_no_format", "0039030726400"),
    ],
)
def test_invalid_mbl(sub, mbl_no, sample_loader):
    httptext = sample_loader.read_file(sub, "sample.html")

    option = ContentRule.build_request_option(
        search_nos=[mbl_no],
        task_ids=["1"],
    )

    response = TextResponse(
        url=option.url,
        body=httptext,
        encoding="utf-8",
        request=Request(url=option.url, meta=option.meta),
    )

    results = [CargoTrackingRoutingRule._is_mbl_no_invalid(response=response)]

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verifier = verify_module.Verifier()
    verifier.verify(results=results)
