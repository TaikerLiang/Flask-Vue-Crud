from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.spiders.carrier_eglv_multi import BookingMainInfoRoutingRule
from test.spiders.carrier_eglv_multi import booking_main_info


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=booking_main_info, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    'sub,booking_no,',
    [
        ('01_basic', '110381781'),
    ],
)
def test_main_info_handler(sub, booking_no, sample_loader):
    httptext = sample_loader.read_file(sub, 'sample.html')

    option = BookingMainInfoRoutingRule.build_request_option(booking_no=booking_no, verification_code='', task_id='1')

    response = TextResponse(
        url=option.url,
        body=httptext,
        encoding='utf-8',
        request=Request(
            url=option.url,
            meta=option.meta
        ),
    )

    rule = BookingMainInfoRoutingRule()
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verifier = verify_module.Verifier()
    verifier.verify(results=results)

