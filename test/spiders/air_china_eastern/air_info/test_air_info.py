from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.spiders.air_china_eastern import AirInfoRoutingRule
from test.spiders.air_china_eastern import air_info


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=air_info, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    'sub,mawb_no',
    [
        ('01_basic', '81231625'),
        ('02_data_not_found', '81375673'),
    ],
)
def test_air_info_handle(sub, mawb_no, sample_loader):
    json_text = sample_loader.read_file(sub, 'AIR_INFO.json')

    option = AirInfoRoutingRule.build_request_option(mawb_no=mawb_no, task_id='1', token='')

    response = TextResponse(
        url=option.url,
        body=json_text,
        encoding='utf-8',
        request=Request(
            url=option.url,
            meta=option.meta,
        ),
    )

    routing_rule = AirInfoRoutingRule()
    results = list(routing_rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)

