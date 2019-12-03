from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_carrier.exceptions import CarrierInvalidMblNoError
from crawler.core_carrier.rules import RuleManager
from crawler.spiders.carrier_cosu import BookingMainInfoRoutingRule
from src.crawler.spiders import carrier_cosu

from test.spiders.carrier_cosu import booking_main_info


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=booking_main_info, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,mbl_no', [
    ('01_booking', '6216853000'),
])
def test_parse_booking_main_info(sample_loader, sub, mbl_no):
    json_text = sample_loader.read_file(sub, 'main_information.json')

    url = f'http://elines.coscoshipping.com/ebtracking/public/booking/{mbl_no}?timestamp=0000000000'

    resp = TextResponse(
        url=url,
        encoding='utf-8',
        body=json_text,
        request=Request(url=url, meta={
            'mbl_no': mbl_no,
            RuleManager.META_CARRIER_CORE_RULE_NAME: BookingMainInfoRoutingRule.name,
        })
    )

    # action
    spider = carrier_cosu.CarrierCosuSpider(name=None, mbl_no=mbl_no)
    results = list(spider.parse(resp))

    # assert
    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)


@pytest.mark.parametrize('sub,mbl_no,expect_exception', [
    ('e01_invalid_mbl_no', '6213846642', CarrierInvalidMblNoError),
])
def test_parse_main_info_error(sample_loader, sub, mbl_no, expect_exception):
    json_text = sample_loader.read_file(sub, 'main_information.json')

    url = f'http://elines.coscoshipping.com/ebtracking/public/bill/{mbl_no}?timestamp=0000000000'

    resp = TextResponse(
        url=url,
        encoding='utf-8',
        body=json_text,
        request=Request(url=url, meta={
            'mbl_no': mbl_no,
            RuleManager.META_CARRIER_CORE_RULE_NAME: BookingMainInfoRoutingRule.name,
        })
    )

    # action
    spider = carrier_cosu.CarrierCosuSpider(name=None, mbl_no=mbl_no)

    with pytest.raises(expect_exception):
        spider.parse(resp)

