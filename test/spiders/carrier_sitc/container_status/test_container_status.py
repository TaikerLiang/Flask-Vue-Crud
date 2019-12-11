from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_carrier.rules import RuleManager
from crawler.spiders.carrier_sitc import ContainerStatusRoutingRule, CarrierSitcSpider
from test.spiders.carrier_sitc import container_status
from test.spiders.utils import extract_url_from


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=container_status, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,mbl_no,container_no', [
    ('01_basic', 'SITDNBBK351734', 'TEXU1590997'),
])
def test_container_status_routing_rule(sub, mbl_no, container_no, sample_loader):
    html_text = sample_loader.read_file(sub, 'sample.html')

    routing_request = ContainerStatusRoutingRule.build_routing_request(mbl_no=mbl_no, container_no=container_no)
    url = extract_url_from(routing_request=routing_request)

    response = TextResponse(
        url=url,
        body=html_text,
        encoding='utf-8',
        request=Request(
            url=url,
            meta={
                RuleManager.META_CARRIER_CORE_RULE_NAME: ContainerStatusRoutingRule.name,
                'mbl_no': mbl_no,
                'container_no': container_no,
                'container_key': container_no,
            }
        )
    )

    spider = CarrierSitcSpider(mbl_no=mbl_no)
    results = list(spider.parse(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)
