from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_air.exceptions import AirInvalidMawbNoError
from crawler.spiders.air_eva import AirInfoRoutingRule
from test.spiders.air_eva import air_info


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=air_info, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    'sub,mawb_no',
    [
        ('01_basic', '28809955'),
    ],
)
def test_air_info_handle(sub, mawb_no, sample_loader):
    json_text = sample_loader.read_file(sub, 'AIR_INFO.json')

    option = AirInfoRoutingRule.build_request_option(mawb_no=mawb_no)

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


@pytest.mark.parametrize(
    'sub,mawb_no,expect_exception',
    [
        ('e01_invalid_mawb_no', '24413956', AirInvalidMawbNoError),
    ],
)
def test_air_info_handler_mawb_no_error(sub, mawb_no, expect_exception, sample_loader):
    json_text = sample_loader.read_file(sub, 'AIR_INFO.json')

    option = AirInfoRoutingRule.build_request_option(mawb_no=mawb_no)

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

    with pytest.raises(expect_exception):
        list(routing_rule.handle(response=response))
