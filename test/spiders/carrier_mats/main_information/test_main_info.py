from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_carrier.exceptions import CarrierInvalidMblNoError
from crawler.spiders.carrier_mats import MainInfoRoutingRule
from test.spiders.carrier_mats import main_information


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=main_information, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,mbl_no,', [
    ('01_one_container', '9271590000'),
    ('02_multiple_container_with_same_name', '5432696000'),
])
def test_main_info_handler(sub, mbl_no, sample_loader):
    json_text = sample_loader.read_file(sub, 'main_information.json')

    url = f'https://www.matson.com/vcsc/tracking/bill/{mbl_no}'

    response = TextResponse(
        url=url,
        body=json_text,
        encoding='utf-8',
        request=Request(
            url=url,
            meta={
                'mbl_no': mbl_no,
            }
        )
    )

    routing_rule = MainInfoRoutingRule()
    results = list(routing_rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)


@pytest.mark.parametrize('sub,mbl_no,expect_exception', [
    ('e01_invalid_mbl_no', '9069059001', CarrierInvalidMblNoError),
])
def test_main_info_handler_mbl_no_error(sub, mbl_no, expect_exception, sample_loader):
    json_text = sample_loader.read_file(sub, 'main_information.json')

    url = f'https://www.matson.com/vcsc/tracking/bill/{mbl_no}'

    response = TextResponse(
        url=url,
        body=json_text,
        encoding='utf-8',
        request=Request(
            url=url,
            meta={
                'mbl_no': mbl_no,
            }
        )
    )

    routing_rule = MainInfoRoutingRule()

    with pytest.raises(expect_exception):
        list(routing_rule.handle(response=response))
