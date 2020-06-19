from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_carrier.exceptions import CarrierInvalidMblNoError
from crawler.core_carrier.rules import RuleManager
from crawler.spiders.carrier_whlc import ListRoutingRule
from test.spiders.carrier_whlc import container_list


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=container_list, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,mbl_no', [
    ('01_single_container', '0249538702'),
    ('02_multiple_container', '0349531933'),
    ('03_no_more_detail', '0249558425'),
])
def test_list_routing_rule(sub, mbl_no, sample_loader):
    html_text = sample_loader.read_file(sub, 'sample.html')

    option = ListRoutingRule.build_request_option(mbl_no=mbl_no, view_state='')

    response = TextResponse(
        url=option.url,
        body=html_text,
        encoding='utf-8',
        request=Request(
            url=option.url,
            meta={
                RuleManager.META_CARRIER_CORE_RULE_NAME: ListRoutingRule.name,
                'mbl_no': mbl_no,
                'cookies': {'123': '123'}
            }
        )
    )

    routing_rule = ListRoutingRule()
    results = list(routing_rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)


@pytest.mark.parametrize('sub,mbl_no,expect_exception', [
    ('e01_invalid_mbl_no', '0249538703', CarrierInvalidMblNoError),
])
def test_list_error(sub, mbl_no, expect_exception, sample_loader):
    html_text = sample_loader.read_file(sub, 'sample.html')

    option = ListRoutingRule.build_request_option(mbl_no=mbl_no, view_state='')

    response = TextResponse(
        url=option.url,
        body=html_text,
        encoding='utf-8',
        request=Request(
            url=option.url,
            meta={
                RuleManager.META_CARRIER_CORE_RULE_NAME: ListRoutingRule.name,
                'mbl_no': mbl_no,
                'cookies': {'123': '123'}
            }
        )
    )

    routing_rule = ListRoutingRule()

    with pytest.raises(expect_exception):
        list(routing_rule.handle(response=response))
