from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_carrier.exceptions import CarrierInvalidMblNoError
from crawler.spiders.carrier_12lu import ContainerStatusRoutingRule
from test.spiders.carrier_12lu import container_status
from test.spiders.utils import extract_url_from


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=container_status, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,mbl_no,page_no', [
    ('01_single_container', 'NOSNB9GX16042', 1),
    ('02_1_multiple_containers', 'NOSNB9TZ35829', 1),
    ('02_2_multiple_containers', 'NOSNB9TZ35829', 2),
])
def test_container_status_routing_rule(sub, mbl_no, page_no, sample_loader):
    json_text = sample_loader.read_file(sub, 'sample.json')

    routing_request = ContainerStatusRoutingRule.build_routing_request(mbl_no=mbl_no, page_no=page_no)
    url = extract_url_from(routing_request=routing_request)

    response = TextResponse(
        url=url,
        body=json_text,
        encoding='utf-8',
        request=Request(
            url=url,
            meta={
                'mbl_no': mbl_no,
                'page_no': page_no,
            }
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

    routing_request = ContainerStatusRoutingRule.build_routing_request(mbl_no=mbl_no, page_no=page_no)
    url = extract_url_from(routing_request=routing_request)

    response = TextResponse(
        url=url,
        body=json_text,
        encoding='utf-8',
        request=Request(
            url=url,
            meta={
                'mbl_no': mbl_no,
                'page_no': page_no,
            }
        )
    )

    routing_rule = ContainerStatusRoutingRule()

    with pytest.raises(expect_exception):
        list(routing_rule.handle(response=response))
