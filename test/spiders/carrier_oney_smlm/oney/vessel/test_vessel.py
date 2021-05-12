from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.spiders.carrier_oney_smlm import CarrierOneySpider, VesselRoutingRule
from test.spiders.carrier_oney_smlm.oney import vessel


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=vessel, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    'sub,mbl_no,bkg_no',
    [
        ('01_single_vessel', 'SH9FSK690300', 'SH9FSK690300'),
        ('02_multiple_vessels', 'SZPVF2740514', 'SZPVF2740514'),
        ('03_no_vessel', 'RICAT4995700', 'RICAT4995700'),
    ],
)
def test_vessel_handle(sub, mbl_no, bkg_no, sample_loader):
    jsontext = sample_loader.read_file(sub, 'sample.json')

    option = VesselRoutingRule.build_request_option(booking_no=bkg_no, base_url=CarrierOneySpider.base_url)

    response = TextResponse(
        url=option.url,
        body=jsontext,
        encoding='utf-8',
        request=Request(
            url=option.url,
        ),
    )

    rule = VesselRoutingRule()
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)
