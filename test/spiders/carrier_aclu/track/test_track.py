from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.spiders.carrier_aclu import TrackRoutingRule
from test.spiders.carrier_aclu import track


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=track, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    "sub,mbl_no,ip",
    [
        ("01_basic", "SA00715282", "1.200.40.75"),
        ("02_invalid_mbl_no", "SA007152822", "1.200.40.75"),
    ],
)
def test_track_routing_rule(sub, mbl_no, ip, sample_loader):
    httptext = sample_loader.read_file(sub, "sample.html")

    option = TrackRoutingRule.build_request_option(mbl_no=mbl_no, ip=ip)

    response = TextResponse(
        url=option.url,
        body=httptext,
        encoding="utf-8",
        request=Request(
            url=option.url,
            meta=option.meta,
        ),
    )

    rule = TrackRoutingRule()
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verify_module.verify(results=results)
