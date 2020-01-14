from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_carrier.exceptions import CarrierInvalidMblNoError
from crawler.core_carrier.rules import RuleManager
from crawler.spiders.carrier_aplu_cmdu_anlc import FirstTierRoutingRule, CarrierCmduSpider
from test.spiders.carrier_aplu_cmdu_anlc.cmdu import main_info
from test.spiders.utils import extract_url_from


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=main_info, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,mbl_no', [
    ('01_not_finish', 'CNPC001499'),
    ('02_finish', 'NBSF300899'),
    ('03_multiple_containers', 'NBSF301194'),
    ('04_por', 'GGZ1004320'),
    ('05_dest', 'NBSF301068'),
])
def test_first_tier_routing_rule(sample_loader, sub, mbl_no):
    html_text = sample_loader.read_file(sub, 'main_info.html')

    routing_request = FirstTierRoutingRule.build_routing_request(mbl_no=mbl_no, base_url=CarrierCmduSpider.base_url)
    url = extract_url_from(routing_request=routing_request)

    response = TextResponse(
        url=url,
        encoding='utf-8',
        body=html_text,
        request=Request(
            url=url,
            meta={
                'mbl_no': mbl_no,
            }
        )
    )

    routing_rule = FirstTierRoutingRule(base_url='http://www.cma-cgm.com')
    results = list(routing_rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)


@pytest.mark.parametrize('sub,mbl_no,expect_exception', [
    ('e01_invalid_mbl_no', 'NBSF300898', CarrierInvalidMblNoError),
])
def test_first_tier_routing_rule_error(sample_loader, sub, mbl_no, expect_exception):
    html_text = sample_loader.read_file(sub, 'main_info.html')

    routing_request = FirstTierRoutingRule.build_routing_request(mbl_no=mbl_no, base_url=CarrierCmduSpider.base_url)
    url = extract_url_from(routing_request=routing_request)

    response = TextResponse(
        url=url,
        encoding='utf-8',
        body=html_text,
        request=Request(
            url=url,
            meta={
                RuleManager.META_CARRIER_CORE_RULE_NAME: FirstTierRoutingRule.name,
                'mbl_no': mbl_no,
            }
        )
    )

    routing_rule = FirstTierRoutingRule(base_url='http://www.cma-cgm.com')

    with pytest.raises(expect_exception):
        list(routing_rule.handle(response=response))
