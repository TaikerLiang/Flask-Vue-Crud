from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_carrier.exceptions import CarrierInvalidMblNoError
from crawler.core_carrier.rules import RuleManager
from crawler.spiders.carrier_gosu_ssph import MainInfoRoutingRule
from test.spiders.carrier_gosu_ssph.ssph import main_info


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=main_info, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    'sub,mbl_no,',
    [
        ('01_basic', 'SSPHSEM8070851'),
    ],
)
def test_main_info_routing_rule(sub, mbl_no, sample_loader):
    json_text = sample_loader.read_file(sub, 'sample.html')

    option = MainInfoRoutingRule.build_request_option(mbl_no=mbl_no)

    response = TextResponse(
        url=option.url,
        body=json_text,
        encoding='utf-8',
        request=Request(
            url=option.url,
            meta={
                RuleManager.META_CARRIER_CORE_RULE_NAME: MainInfoRoutingRule.name,
            },
        ),
    )

    routing_rule = MainInfoRoutingRule()
    results = list(routing_rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)


@pytest.mark.parametrize(
    'sub,mbl_no,expect_exception',
    [
        ('e01_invalid_mbl_no', 'SSPHSEM8070850', CarrierInvalidMblNoError),
    ],
)
def test_main_info_handler_mbl_no_error(sub, mbl_no, expect_exception, sample_loader):
    json_text = sample_loader.read_file(sub, 'sample.html')

    option = MainInfoRoutingRule.build_request_option(mbl_no=mbl_no)

    response = TextResponse(
        url=option.url,
        body=json_text,
        encoding='utf-8',
        request=Request(
            url=option.url,
            meta={
                RuleManager.META_CARRIER_CORE_RULE_NAME: MainInfoRoutingRule.name,
            },
        ),
    )

    routing_rule = MainInfoRoutingRule()

    with pytest.raises(expect_exception):
        list(routing_rule.handle(response=response))
