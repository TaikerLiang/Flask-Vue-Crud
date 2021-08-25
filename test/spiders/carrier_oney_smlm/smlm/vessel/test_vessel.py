from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.spiders.carrier_smlm import CarrierSmlmSpider
from crawler.core_carrier.oney_smlm_share_spider import VesselRoutingRule
from test.spiders.carrier_oney_smlm.smlm import vessel


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=vessel, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    'sub,mbl_no,bkg_no',
    [
        ('01_single_vessel', 'SHSM9C747300', 'SHSM9C747300'),
        ('02_multiple_vessels', 'TATH9C294100', 'TATH9C294100'),
    ],
)
def test_vessel_routing_handle(sub, mbl_no, bkg_no, sample_loader):
    jsontext = sample_loader.read_file(sub, 'sample.json')

    option = VesselRoutingRule.build_request_option(booking_no=bkg_no, base_url=CarrierSmlmSpider.base_url)

    response = TextResponse(
        url=option.url,
        body=jsontext,
        encoding='utf-8',
        request=Request(
            url=option.url,
            meta=option.meta,
        ),
    )

    rule = VesselRoutingRule()
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)
