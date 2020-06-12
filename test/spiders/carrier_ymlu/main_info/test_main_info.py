from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_carrier.exceptions import CarrierInvalidMblNoError
from crawler.core_carrier.rules import RuleManager
from crawler.spiders.carrier_ymlu import MainInfoRoutingRule
from test.spiders.carrier_ymlu import main_info


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=main_info, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,mbl_no,', [
    ('01_all_exist', 'W216104890'),
    ('02_no_xta', 'W209047989'),
    ('03_no_release', 'I209365239'),
    ('04_multi_containers', 'W241061370'),
    ('05_with_firm_code', 'W226020752'),
    ('06_ip_blocked', 'E209048375'),
    ('07_delivery_without_time_status', 'W209139591')
])
def test_main_info_routing_rule(sub, mbl_no, sample_loader):
    httptext = sample_loader.read_file(sub, 'sample.html')

    request_option = MainInfoRoutingRule.build_request_option(mbl_no=mbl_no)

    response = TextResponse(
        url=request_option.url,
        body=httptext,
        encoding='utf-8',
        request=Request(
            url=request_option.url,
            meta={'mbl_no': mbl_no}
        )
    )

    rule = MainInfoRoutingRule()
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)


@pytest.mark.parametrize('sub,mbl_no,expect_exception', [
    ('e01_invalid_mbl_no', 'W216098981', CarrierInvalidMblNoError),
])
def test_main_info_handler_mbl_no_error(sub, mbl_no, expect_exception, sample_loader):
    httptext = sample_loader.read_file(sub, 'sample.html')

    request_option = MainInfoRoutingRule.build_request_option(mbl_no=mbl_no)

    response = TextResponse(
        url=request_option.url,
        body=httptext,
        encoding='utf-8',
        request=Request(
            url=request_option.url,
            meta={
                RuleManager.META_CARRIER_CORE_RULE_NAME: MainInfoRoutingRule.name,
                'mbl_no': mbl_no,
            }
        )
    )

    rule = MainInfoRoutingRule()
    with pytest.raises(expect_exception):
        list(rule.handle(response=response))
