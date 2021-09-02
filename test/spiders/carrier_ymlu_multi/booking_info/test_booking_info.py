from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.spiders.carrier_ymlu_multi import BookingInfoRoutingRule, HiddenFormSpec
from test.spiders.carrier_ymlu_multi import booking_info


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=booking_info, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    'sub,booking_nos,task_ids',
    [
        ('01_multi_booking_nos', ['FCL147384', 'FCL147097', 'YCH863258', 'YCH857197'], [1, 2, 3, 4]),
        ('02_single_booking_nos', ['YCH857197'], [1]),
        ('03_ip_blocked', ['E209048375'], [1]),
        ('04_no_data_found', ['FCL147384'], [1]),
    ],
)
def test_booking_info_routing_rule(sub, booking_nos, task_ids, sample_loader):
    httptext = sample_loader.read_file(sub, 'sample.html')

    request_option = BookingInfoRoutingRule.build_request_option(
        task_ids=task_ids,
        booking_nos=booking_nos,
        hidden_form_spec=HiddenFormSpec(view_state_generator='', view_state='', event_validation='', previous_page=''),
        captcha='',
        headers={},
    )

    response = TextResponse(
        url=request_option.url,
        body=httptext,
        encoding='utf-8',
        request=Request(
            url=request_option.url,
            meta=request_option.meta,
        ),
    )

    rule = BookingInfoRoutingRule()
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)

