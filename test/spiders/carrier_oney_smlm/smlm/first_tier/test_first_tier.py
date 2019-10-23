from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_carrier.exceptions import CarrierInvalidMblNoError
from crawler.core_carrier.rules import RuleManager
from crawler.spiders.carrier_oney_smlm import FirstTierRoutingRule, CarrierSmlmSpider
from test.spiders.carrier_oney_smlm.smlm import first_tier
from test.spiders.utils import extract_url_from


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=first_tier, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,mbl_no,base_url', [
    ('01_single_container', 'SHSM9C747300', CarrierSmlmSpider.base_url),
    ('02_multiple_containers', 'SHFA9A128100', CarrierSmlmSpider.base_url),
])
def test_first_tier_routing_rule(sub, mbl_no, base_url, sample_loader):
    jsontext = sample_loader.read_file(sub, 'sample.json')

    routing_request = FirstTierRoutingRule.build_routing_request(mbl_no=mbl_no, base_url=base_url)
    url = extract_url_from(routing_request=routing_request)

    response = TextResponse(
        url=url,
        body=jsontext,
        encoding='utf-8',
        request=Request(
            url=url,
            meta={
                RuleManager.META_CARRIER_CORE_RULE_NAME: FirstTierRoutingRule.name,
            }
        )
    )

    spider = CarrierSmlmSpider(mbl_no=mbl_no)
    results = list(spider.parse(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)


@pytest.mark.parametrize('sub,mbl_no,base_url,expect_exception', [
    ('e01_invalid_mbl_no', 'SHFA9A128101', CarrierSmlmSpider.base_url, CarrierInvalidMblNoError),
])
def test_first_tier_routing_rule_mbl_no_error(sub, mbl_no, base_url, expect_exception, sample_loader):
    jsontext = sample_loader.read_file(sub, 'sample.json')

    routing_request = FirstTierRoutingRule.build_routing_request(mbl_no=mbl_no, base_url=base_url)
    url = extract_url_from(routing_request=routing_request)

    response = TextResponse(
        url=url,
        body=jsontext,
        encoding='utf-8',
        request=Request(
            url=url,
            meta={
                RuleManager.META_CARRIER_CORE_RULE_NAME: FirstTierRoutingRule.name,
            }
        )
    )

    spider = CarrierSmlmSpider(mbl_no=mbl_no)
    with pytest.raises(expect_exception):
        list(spider.parse(response=response))
