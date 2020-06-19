from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_carrier.exceptions import CarrierInvalidMblNoError
from crawler.spiders.carrier_sitc import BasicInfoRoutingRule
from test.spiders.carrier_sitc import basic_info


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=basic_info, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,mbl_no,container_no_list', [
    ('01_basic', 'SITDNBBK351734', ['TEXU1590997']),
])
def test_main_info_routing_rule(sub, mbl_no, container_no_list, sample_loader):
    json_text = sample_loader.read_file(sub, 'sample.json')

    option = BasicInfoRoutingRule.build_request_option(mbl_no=mbl_no, container_no_list=container_no_list)

    container_no = container_no_list[0]
    other_container_no_list = container_no_list[1:]

    response = TextResponse(
        url=option.url,
        body=json_text,
        encoding='utf-8',
        request=Request(
            url=option.url,
            meta={
                'mbl_no': mbl_no,
                'container_no': container_no,
                'container_no_list': other_container_no_list,
            }
        )
    )

    routing_rule = BasicInfoRoutingRule()
    results = list(routing_rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)


@pytest.mark.parametrize('sub,mbl_no,container_no_list,expect_exception', [
    ('e01_invalid_mbl_no', 'SITDNBBK351734', ['TEXU1590990'], CarrierInvalidMblNoError),
])
def test_main_info_handler_mbl_no_error(sub, mbl_no, container_no_list, expect_exception, sample_loader):
    json_text = sample_loader.read_file(sub, 'sample.json')

    option = BasicInfoRoutingRule.build_request_option(mbl_no=mbl_no, container_no_list=container_no_list)

    container_no = container_no_list[0]
    other_container_no_list = container_no_list[1:]

    response = TextResponse(
        url=option.url,
        body=json_text,
        encoding='utf-8',
        request=Request(
            url=option.url,
            meta={
                'mbl_no': mbl_no,
                'container_no': container_no,
                'container_no_list': other_container_no_list,
            }
        )
    )

    routing_rule = BasicInfoRoutingRule()

    with pytest.raises(expect_exception):
        list(routing_rule.handle(response=response))