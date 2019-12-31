from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_carrier.rules import RuleManager
from crawler.spiders.carrier_hdmu import AvailabilityRoutingRule, CookiesRoutingRule, CarrierHdmuSpider
from test.spiders.carrier_hdmu import availability
from test.spiders.utils import extract_url_from


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=availability, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,mbl_no,container_no', [
    ('01_first', 'TAWB0789799', 'CAIU7479659'),
])
def test_availability_routing_rule(sub, mbl_no, sample_loader, container_no):
    html_text = sample_loader.read_file(sub, 'sample.html')

    routing_request = AvailabilityRoutingRule.build_routing_request(
        mbl_no=mbl_no, container_no=container_no, callback=CookiesRoutingRule.retry)
    url = extract_url_from(routing_request=routing_request)

    response = TextResponse(
        url=url,
        body=html_text,
        encoding='utf-8',
        request=Request(
            url=url,
            meta={
                RuleManager.META_CARRIER_CORE_RULE_NAME: AvailabilityRoutingRule.name,
                'mbl_no': mbl_no,
                'container_no': container_no,
            }
        )
    )

    spider = CarrierHdmuSpider(mbl_no=mbl_no)
    results = list(spider.parse(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)
