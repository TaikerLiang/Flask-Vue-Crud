from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_carrier.exceptions import CarrierInvalidMblNoError
from crawler.spiders.carrier_12lu import ContainerStatusRoutingRule
from test.spiders.carrier_12lu import container_status


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=container_status, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,mbl_no,page_no', [
    ('01_single_container', 'NOSNB9GX16042', 1),
    ('02_multiple_pages_not_finished', 'NOSNB9TZ35829', 1),
    ('03_multiple_pages_finished', 'NOSNB9TZ35829', 2),
])
def test_container_status_handle(sub, mbl_no, page_no, sample_loader):
    json_text = sample_loader.read_file(sub, 'sample.json')

    option = ContainerStatusRoutingRule.build_request_option(mbl_no=mbl_no, page_no=page_no)

    response = TextResponse(
        url=option.url,
        body=json_text,
        encoding='utf-8',
        request=Request(
            url=option.url,
            meta=option.meta,
        )
    )

    routing_rule = ContainerStatusRoutingRule()
    results = list(routing_rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)


@pytest.mark.parametrize('sub,mbl_no,page_no,expect_exception', [
    ('e01_invalid_mbl_no', 'NOSNB9GX1604', 1, CarrierInvalidMblNoError),
])
def test_container_status_handler_mbl_no_error(sub, mbl_no, page_no, expect_exception, sample_loader):
    json_text = sample_loader.read_file(sub, 'sample.json')

    option = ContainerStatusRoutingRule.build_request_option(mbl_no=mbl_no, page_no=page_no)

    response = TextResponse(
        url=option.url,
        body=json_text,
        encoding='utf-8',
        request=Request(
            url=option.url,
            meta=option.meta,
        )
    )

    routing_rule = ContainerStatusRoutingRule()

    with pytest.raises(expect_exception):
        list(routing_rule.handle(response=response))
