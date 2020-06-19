from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_carrier.rules import RuleManager
from crawler.spiders.carrier_sitc import VesselInfoRoutingRule
from test.spiders.carrier_sitc import vessel_info


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=vessel_info, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,mbl_no,container_no', [
    ('01_single_vessel', 'SITDNBBK351734', 'TEXU1590997'),
    ('02_multiple_vessel', 'SITDNBHP351657', 'TEXU1590148'),
])
def test_vessel_info_routing_rule(sub, mbl_no, container_no, sample_loader):
    json_text = sample_loader.read_file(sub, 'sample.json')

    option = VesselInfoRoutingRule.build_request_option(mbl_no=mbl_no, container_no=container_no)

    response = TextResponse(
        url=option.url,
        body=json_text,
        encoding='utf-8',
        request=Request(
            url=option.url,
            meta={
                RuleManager.META_CARRIER_CORE_RULE_NAME: VesselInfoRoutingRule.name,
                'mbl_no': mbl_no,
                'container_no': container_no,
            }
        )
    )

    routing_rule = VesselInfoRoutingRule()
    results = list(routing_rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)
