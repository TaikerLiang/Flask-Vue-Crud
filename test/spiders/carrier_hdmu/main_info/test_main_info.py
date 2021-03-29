from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_carrier.base import SHIPMENT_TYPE_MBL
from crawler.core_carrier.exceptions import CarrierInvalidMblNoError, CarrierResponseFormatError, \
    CarrierInvalidSearchNoError
from crawler.spiders.carrier_hdmu import MainRoutingRule, ItemRecorder
from test.spiders.carrier_hdmu import main_info


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=main_info, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,mbl_no', [
    ('01_one_container', 'GJWB1899760'),
    ('02_multiple_containers', 'QSWB8011462'),
    ('03_availability', 'TAWB0789799'),
    ('04_red_time', 'NXWB1903966'),
    ('05_1_without_lfd', 'QSWB8011632'),
    ('05_2_without_lfd', 'QSWB8011630'),
    ('06_1_original_bl', 'KETC0876470'),
    ('06_2_original_bl', 'QSLB8267628'),
    ('07_without_cargo_delivery_information', 'TYWB0924004')
])
def test_main_routing_rule(sample_loader, sub, mbl_no):
    html_text = sample_loader.read_file(sub, 'sample.html')

    option = MainRoutingRule.build_request_option(search_no=mbl_no, search_type=SHIPMENT_TYPE_MBL, cookies={})

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
    rule = MainRoutingRule(item_recorder, search_type=SHIPMENT_TYPE_MBL)
    request_options = list(rule.handle(response=response))
    results = item_recorder.items + request_options

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)


@pytest.mark.parametrize('sub,mbl_no,expect_exception', [
    ('e01_invalid_mbl', 'QSWB801163', CarrierInvalidSearchNoError),
    ('e02_change_header', 'GJWB1899760', CarrierResponseFormatError),
])
def test_main_routing_rule_error(sample_loader, sub, mbl_no, expect_exception):
    html_text = sample_loader.read_file(sub, 'sample.html')

    option = MainRoutingRule.build_request_option(
        search_no=mbl_no, search_type=SHIPMENT_TYPE_MBL, cookies={}, under_line=True)

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
    rule = MainRoutingRule(item_recorder, search_type=SHIPMENT_TYPE_MBL)
    with pytest.raises(expect_exception):
        list(rule.handle(response))
