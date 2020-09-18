from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_carrier.exceptions import CarrierInvalidMblNoError
from crawler.spiders.carrier_oolu import CargoTrackingRule
from test.spiders.carrier_oolu import cargo_tracking


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=cargo_tracking, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,mbl_no', [
    ('01_single_container', '2625845270'),
    ('02_multi_containers', '2109051600'),
    ('03_without_custom_release_date', '2628633440'),
    ('04_tranship_exist', '2630699272'),
    ('05_custom_release_title_exist_but_value_empty', '2635541720'),
])
def test_cargo_tracking_handler(sub, mbl_no, sample_loader):
    html_file = sample_loader.read_file(sub, 'sample.html')

    option = CargoTrackingRule.build_request_option(mbl_no=mbl_no)
    response = TextResponse(
        url=option.url,
        body=html_file,
        encoding='utf-8',
        request=Request(
            url=option.url,
            meta=option.meta,
        )
    )

    rule = CargoTrackingRule(driver=None)
    results = list(rule._handle_response(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)


@pytest.mark.parametrize('sub,mbl_no,expect_exception', [
    ('e01_invalid_mbl_no', 'OOLU0000000000', CarrierInvalidMblNoError),
])
def test_cargo_tracking_handler_no_mbl_error(sub, mbl_no, expect_exception, sample_loader):
    html_file = sample_loader.read_file(sub, 'sample.html')

    option = CargoTrackingRule.build_request_option(mbl_no=mbl_no)

    response = TextResponse(
        url=option.url,
        body=html_file,
        encoding='utf-8',
        request=Request(
            url=option.url,
            meta=option.meta,
        )
    )

    rule = CargoTrackingRule(driver=None)
    with pytest.raises(expect_exception):
        list(rule._handle_response(response=response))
