from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.spiders.carrier_oney_smlm import CarrierOneySpider, RailInfoRoutingRule
from test.spiders.carrier_oney_smlm.oney import rail_info
from test.spiders.utils import extract_url_from


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=rail_info, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,mbl_no,cntr_no,cop_no', [
    ('01', 'SZPVD5837613', 'BEAU5297455', 'CSZP9819161088'),
])
def test_rail_information_routing_rule(sub, mbl_no, cntr_no, cop_no, sample_loader):
    jsontext = sample_loader.read_file(sub, 'sample.json')

    routing_request = RailInfoRoutingRule.build_routing_request(
        container_no=cntr_no, cooperation=cop_no, base_url=CarrierOneySpider.base_url)
    url = extract_url_from(routing_request=routing_request)

    response = TextResponse(
        url=url,
        body=jsontext,
        encoding='utf-8',
        request=Request(
            url=url,
            meta={
                'container_key': cntr_no
            }
        )
    )

    rule = RailInfoRoutingRule()
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)
