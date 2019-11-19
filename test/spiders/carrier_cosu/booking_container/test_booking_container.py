from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_carrier.rules import RuleManager
from crawler.spiders.carrier_cosu import BookingContainerRoutingRule
from src.crawler.spiders import carrier_cosu
from test.spiders.carrier_cosu import booking_container


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=booking_container, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,booking_no', [
    ('01_container', '6225172110'),
])
def test_container(sample_loader, sub, booking_no):
    json_text = sample_loader.read_file(sub, 'container.json')

    container_url = (
        f'http://elines.coscoshipping.com/ebtracking/public/booking/containers/{booking_no}?timestamp=0000000000'
    )

    resp = TextResponse(
        url=container_url,
        encoding='utf-8',
        body=json_text,
        request=Request(url=container_url, meta={
            'mbl_no': booking_no,
            RuleManager.META_CARRIER_CORE_RULE_NAME: BookingContainerRoutingRule.name,
        })
    )

    # action
    spider = carrier_cosu.CarrierCosuSpider(name=None, mbl_no=booking_no)
    results = list(spider.parse(resp))

    # assert
    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results, booking_no=booking_no)
