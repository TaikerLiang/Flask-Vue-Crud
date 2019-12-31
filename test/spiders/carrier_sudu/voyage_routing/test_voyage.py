from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_carrier.rules import RuleManager
from crawler.spiders.carrier_sudu import BasicRequestSpec, CarrierSuduSpider, VoyageRoutingRule
from test.spiders.carrier_sudu import voyage_routing
from test.spiders.utils import extract_url_from


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=voyage_routing, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,mbl_no,voyage_location, voyage_direction', [
    ('01_pol', 'SUDUN9998ALTNBPS', 'Shanghai CNSHA', 'Departure'),
    ('02_pod', 'SUDUN9998ALTNBPS', 'Houston USHOU', 'Arrival'),
])
def test_voyage_routing_rule(sub, mbl_no, voyage_location, voyage_direction, sample_loader):
    text_text = sample_loader.read_file(sub, 'sample.html')

    basic_request_spec = BasicRequestSpec(mbl_no=mbl_no, view_state='', j_idt='')
    routing_request = VoyageRoutingRule.build_routing_request(
        basic_request_spec=basic_request_spec,
        voyage_key='',
        voyage_location=voyage_location,
        voyage_direction=voyage_direction
    )
    url = extract_url_from(routing_request=routing_request)

    response = TextResponse(
        url=url,
        body=text_text,
        encoding='utf-8',
        request=Request(
            url=url,
            meta={
                RuleManager.META_CARRIER_CORE_RULE_NAME: VoyageRoutingRule.name,
                'voyage_location': voyage_location,
                'voyage_direction': voyage_direction,
                'basic_request_spec': basic_request_spec,
            }
        )
    )

    spider = CarrierSuduSpider(mbl_no=mbl_no)
    results = list(spider.parse(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)
