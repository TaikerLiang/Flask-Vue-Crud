from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.spiders.carrier_ymlu_multi import BookingMainInfoPageRoutingRule, HiddenFormSpec
from test.spiders.carrier_ymlu_multi import booking_main_info


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=booking_main_info, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    'sub,mbl_no,task_id',
    [
        ('01_all_exist', 'W216104890', 1),
        ('02_no_xta', 'W209047989', 1),
        ('03_no_release', 'I209365239', 1),
        ('04_multi_containers', 'W241061370', 1),
        ('05_with_firm_code', 'W226020752', 1),
        ('06_ip_blocked', 'E209048375', 1),
        ('07_delivery_without_time_status', 'W209139591', 1),
        ('08_to_be_advised_ver2', 'W470030608', 1),
        ('09_by_booking_no_and_mbl_no', 'W120511524', 1),
    ],
)
def test_booking_main_info_page_routing_rule(sub, mbl_no, task_id, sample_loader):
    httptext = sample_loader.read_file(sub, 'sample.html')

    request_option = BookingMainInfoPageRoutingRule.build_request_option(
        task_id=task_id,
        follow_url='',
        mbl_no=mbl_no,
        booking_no='',
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

    rule = BookingMainInfoPageRoutingRule()
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)

