from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_carrier.rules import RuleManager
from crawler.spiders.carrier_oney_smlm import CarrierOneySpider, VesselRoutingRule
from test.spiders.carrier_oney_smlm.oney import vessel
from test.spiders.utils import extract_url_from


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=vessel, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,mbl_no,bkg_no', [
    ('01_single_vessel', 'SH9FSK690300', 'SH9FSK690300'),
    ('02_multiple_vessels', 'SZPVF2740514', 'SZPVF2740514'),
])
def test_vessel_routing_rule(sub, mbl_no, bkg_no, sample_loader):
    jsontext = sample_loader.read_file(sub, 'sample.json')

    routing_request = VesselRoutingRule.build_routing_request(booking_no=bkg_no, base_url=CarrierOneySpider.base_url)
    url = extract_url_from(routing_request=routing_request)

    response = TextResponse(
        url=url,
        body=jsontext,
        encoding='utf-8',
        request=Request(
            url=url,
            meta={
                RuleManager.META_CARRIER_CORE_RULE_NAME: VesselRoutingRule.name,
            }
        )
    )

    spider = CarrierOneySpider(mbl_no=mbl_no)
    results = list(spider.parse(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)
