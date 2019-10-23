from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_carrier.rules import RuleManager
from crawler.spiders.carrier_oney_smlm import CarrierOneySpider, RailInfoRoutingRule
from test.spiders.carrier_oney_smlm.oney import rail_info
from test.spiders.utils import extract_url_from


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=rail_info, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,mbl_no,cntr_no,cop_no,base_url', [
    ('01', 'SZPVD5837613', 'BEAU5297455', 'CSZP9819161088', CarrierOneySpider.base_url),
])
def test_rail_information_routing_rule(sub, mbl_no, cntr_no, cop_no, base_url, sample_loader):
    jsontext = sample_loader.read_file(sub, 'sample.json')

    routing_request = RailInfoRoutingRule.build_routing_request(
        container_no=cntr_no, cooperation=cop_no, base_url=base_url)
    url = extract_url_from(routing_request=routing_request)

    response = TextResponse(
        url=url,
        body=jsontext,
        encoding='utf-8',
        request=Request(
            url=url,
            meta={
                RuleManager.META_CARRIER_CORE_RULE_NAME: RailInfoRoutingRule.name,
                'container_key': cntr_no
            }
        )
    )

    spider = CarrierOneySpider(mbl_no=mbl_no)
    results = list(spider.parse(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)
