from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_carrier.base import SHIPMENT_TYPE_MBL
from crawler.spiders.carrier_whlc import BillRoutingRule
from test.spiders.carrier_whlc import container_nos


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=container_nos, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,search_no', [
    ('01_single_container', '027B556005'),
    ('02_multiple_container', '027B555014'),
])
def test_extract_container_nos(sub, search_no, sample_loader):
    html_text = sample_loader.read_file(sub, 'sample.html')

    option = BillRoutingRule.build_request_option(search_no=search_no)

    response = TextResponse(
        url=option.url,
        body=html_text,
        encoding='utf-8',
        request=Request(
            url=option.url,
            meta=option.meta,
        )
    )

    rule = BillRoutingRule(search_type=SHIPMENT_TYPE_MBL)
    results = rule._extract_container_nos(response=response)

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)


@pytest.mark.parametrize('sub,search_no', [
    ('e01_invalid_mbl_no', '0249538703'),
])
def test_list_error(sub, search_no, sample_loader):
    html_text = sample_loader.read_file(sub, 'sample.html')

    option = BillRoutingRule.build_request_option(search_no=search_no)

    response = TextResponse(
        url=option.url,
        body=html_text,
        encoding='utf-8',
        request=Request(
            url=option.url,
            meta=option.meta,
        )
    )

    search_no_invalid = BillRoutingRule._is_search_no_invalid(response=response)
    assert search_no_invalid is True

