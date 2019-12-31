from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_carrier.rules import RuleManager
from crawler.spiders.carrier_hdmu import ContainerRoutingRule, CarrierHdmuSpider, CookiesRoutingRule
from test.spiders.carrier_hdmu import container
from test.spiders.utils import extract_url_from


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=container, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,mbl_no,container_no,container_index', [
    ('01_first', 'QSWB8011462', 'DFSU6717570', 2),
])
def test_container_routing_rule(sub, mbl_no, sample_loader, container_no, container_index):
    html_text = sample_loader.read_file(sub, 'sample.html')

    routing_request = ContainerRoutingRule.build_routing_request(
        mbl_no=mbl_no, container_index=container_index, h_num=0, callback=CookiesRoutingRule.retry)
    url = extract_url_from(routing_request=routing_request)

    response = TextResponse(
        url=url,
        body=html_text,
        encoding='utf-8',
        request=Request(
            url=url,
            meta={
                RuleManager.META_CARRIER_CORE_RULE_NAME: ContainerRoutingRule.name,
                'mbl_no': mbl_no,
                'container_index': container_index,
                'callback': CookiesRoutingRule.retry,
            }
        )
    )

    spider = CarrierHdmuSpider(mbl_no=mbl_no)
    results = list(spider.parse(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)
