from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_carrier.exceptions import CarrierInvalidMblNoError
from crawler.core_carrier.rules import RuleManager
from crawler.spiders.carrier_cmdu import FirstTierRoutingRule
from test.spiders.carrier_cmdu import first_tier


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=first_tier, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    'sub,mbl_no',
    [
        ('01_not_finish', 'CNPC001499'),
        ('02_finish', 'NBSF300899'),
        ('03_multiple_containers', 'NBSF301194'),
        ('04_por', 'GGZ1004320'),
        ('05_dest', 'NBSF301068'),
    ],
)
def test_first_tier_routing_rule(sample_loader, sub, mbl_no):
    html_text = sample_loader.read_file(sub, 'main_info.html')

    option = FirstTierRoutingRule.build_request_option(mbl_no=mbl_no)

    response = TextResponse(
        url=option.url,
        encoding='utf-8',
        body=html_text,
        request=Request(
            url=option.url,
            meta={
                'mbl_no': mbl_no,
            },
        ),
    )

    routing_rule = FirstTierRoutingRule()
    results = list(routing_rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)


@pytest.mark.parametrize(
    'sub,mbl_no,expect_exception',
    [
        ('e01_invalid_mbl_no', 'NBSF300898', CarrierInvalidMblNoError),
    ],
)
def test_first_tier_routing_rule_error(sample_loader, sub, mbl_no, expect_exception):
    html_text = sample_loader.read_file(sub, 'main_info.html')

    option = FirstTierRoutingRule.build_request_option(mbl_no=mbl_no)

    response = TextResponse(
        url=option.url,
        encoding='utf-8',
        body=html_text,
        request=Request(
            url=option.url,
            meta={
                RuleManager.META_CARRIER_CORE_RULE_NAME: FirstTierRoutingRule.name,
                'mbl_no': mbl_no,
            },
        ),
    )

    routing_rule = FirstTierRoutingRule()

    with pytest.raises(expect_exception):
        list(routing_rule.handle(response=response))
