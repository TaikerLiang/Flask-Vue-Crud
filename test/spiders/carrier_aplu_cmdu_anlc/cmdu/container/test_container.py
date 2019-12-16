from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_carrier.rules import RuleManager
from crawler.spiders.carrier_aplu_cmdu_anlc import CarrierCmduSpider, ContainerStatusRoutingRule
from test.spiders.carrier_aplu_cmdu_anlc.cmdu import container
from test.spiders.utils import extract_url_from


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=container, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,mbl_no,container_no', [
    ('01_basic', 'NBSF301194', 'ECMU9893257'),
])
def test_container_status_routing_rule(sample_loader, sub, mbl_no, container_no):
    html_text = sample_loader.read_file(sub, 'container.html')

    routing_request = ContainerStatusRoutingRule.build_routing_request(
        mbl_no=mbl_no, container_no=container_no, base_url=CarrierCmduSpider.base_url)
    url = extract_url_from(routing_request=routing_request)

    response = TextResponse(
        url=url,
        encoding='utf-8',
        body=html_text,
        request=Request(
            url=url,
            meta={
                RuleManager.META_CARRIER_CORE_RULE_NAME: ContainerStatusRoutingRule.name,
                'container_no': container_no,
            },
        ),
    )

    spider = CarrierCmduSpider(name=None, mbl_no=mbl_no)
    results = list(spider.parse(response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)
