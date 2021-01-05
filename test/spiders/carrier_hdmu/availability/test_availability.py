from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.spiders.carrier_hdmu import AvailabilityRoutingRule, ItemRecorder
from test.spiders.carrier_hdmu import availability


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=availability, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,mbl_no,container_no', [
    ('01_first', 'TAWB0789799', 'CAIU7479659'),
    ('02_value_not_exist', 'TYWB0960059', 'BMOU4101393'),
])
def test_availability_routing_rule(sub, mbl_no, sample_loader, container_no):
    html_text = sample_loader.read_file(sub, 'sample.html')

    option = AvailabilityRoutingRule.build_request_option(mbl_no=mbl_no, container_no=container_no, prefix_exist=False)

    response = TextResponse(
        url=option.url,
        body=html_text,
        encoding='utf-8',
        request=Request(
            url=option.url,
            meta=option.meta,
        )
    )

    item_recorder = ItemRecorder()
    rule = AvailabilityRoutingRule(item_recorder)
    rule.handle(response=response)
    results = item_recorder.items

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)
