from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_carrier.exceptions import CarrierInvalidMblNoError
from crawler.core_carrier.rules import RuleManager
from crawler.spiders.carrier_aclu import CarrierAcluSpider, SearchRoutingRule
from test.spiders.carrier_aclu import search
from test.spiders.utils import extract_url_from


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=search, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,mbl_no,', [
    ('01_single_container', 'CRSU9164589'),
    ('02_multi_containers', 'S317458555'),
])
def test_main_info_routing_rule(sub, mbl_no, sample_loader):
    httptext = sample_loader.read_file(sub, 'sample.html')

    routing_request = SearchRoutingRule.build_routing_request(mbl_no=mbl_no)
    url = extract_url_from(routing_request=routing_request)

    response = TextResponse(
        url=url,
        body=httptext,
        encoding='utf-8',
        request=Request(
            url=url,
            meta={
                RuleManager.META_CARRIER_CORE_RULE_NAME: SearchRoutingRule.name,
            }
        )
    )

    spider = CarrierAcluSpider(mbl_no=mbl_no)
    results = list(spider.parse(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)


@pytest.mark.parametrize('sub,mbl_no,expect_exception', [
    ('e01_invalid_mbl_no', 'CRSU9164588', CarrierInvalidMblNoError),
    ('e02_mbl_no_not_activate', 'GCNU4723103', CarrierInvalidMblNoError),
])
def test_main_info_handler_mbl_no_error(sub, mbl_no, expect_exception, sample_loader):
    httptext = sample_loader.read_file(sub, 'sample.html')

    routing_request = SearchRoutingRule.build_routing_request(mbl_no=mbl_no)
    url = extract_url_from(routing_request=routing_request)

    response = TextResponse(
        url=url,
        body=httptext,
        encoding='utf-8',
        request=Request(
            url=url,
            meta={
                RuleManager.META_CARRIER_CORE_RULE_NAME: SearchRoutingRule.name,
            }
        )
    )

    spider = CarrierAcluSpider(mbl_no=mbl_no)
    with pytest.raises(expect_exception):
        list(spider.parse(response=response))
