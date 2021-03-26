from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_carrier.base import SHIPMENT_TYPE_MBL
from crawler.core_carrier.exceptions import CarrierInvalidMblNoError, CarrierInvalidSearchNoError
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
    ('06_detail_table_not_exist', '2650422090'),
])
def test_cargo_tracking_handler(sub, mbl_no, sample_loader):
    html_file = sample_loader.read_file(sub, 'sample.html')

    option = CargoTrackingRule.build_request_option(search_no=mbl_no)
    response = TextResponse(
        url=option.url,
        body=html_file,
        encoding='utf-8',
        request=Request(
            url=option.url,
            meta=option.meta,
        )
    )

    results = list(CargoTrackingRule._handle_response(response=response, search_type=SHIPMENT_TYPE_MBL))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)


@pytest.mark.parametrize('sub,mbl_no,expect_exception', [
    ('e01_invalid_mbl_no', 'OOLU0000000000', CarrierInvalidSearchNoError),
])
def test_cargo_tracking_handler_no_mbl_error(sub, mbl_no, expect_exception, sample_loader):
    html_file = sample_loader.read_file(sub, 'sample.html')

    option = CargoTrackingRule.build_request_option(search_no=mbl_no)

    response = TextResponse(
        url=option.url,
        body=html_file,
        encoding='utf-8',
        request=Request(
            url=option.url,
            meta=option.meta,
        )
    )

    with pytest.raises(expect_exception):
        list(CargoTrackingRule._handle_response(response=response, search_type=SHIPMENT_TYPE_MBL))
