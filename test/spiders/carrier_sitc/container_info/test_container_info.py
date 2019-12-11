from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_carrier.rules import RuleManager
from crawler.spiders.carrier_sitc import CarrierSitcSpider, ContainerInfoRoutingRule
from test.spiders.carrier_sitc import container_info
from test.spiders.utils import extract_url_from


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=container_info, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,mbl_no,container_no', [
    ('01_single_container', 'SITDNBBK351600', 'TEXU1585331'),
    ('02_multiple_container', 'SITDNBBK351734', 'TEXU1590997'),
])
def test_container_info_routing_rule(sub, mbl_no, container_no, sample_loader):
    json_text = sample_loader.read_file(sub, 'sample.json')

    routing_request = ContainerInfoRoutingRule.build_routing_request(mbl_no=mbl_no, container_no=container_no)
    url = extract_url_from(routing_request=routing_request)

    response = TextResponse(
        url=url,
        body=json_text,
        encoding='utf-8',
        request=Request(
            url=url,
            meta={
                RuleManager.META_CARRIER_CORE_RULE_NAME: ContainerInfoRoutingRule.name,
                'mbl_no': mbl_no,
            }
        )
    )

    spider = CarrierSitcSpider(mbl_no=mbl_no)
    results = list(spider.parse(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)
