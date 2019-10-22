from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_carrier.exceptions import CarrierInvalidMblNoError
from crawler.core_carrier.rules import RuleManager
from crawler.spiders.carrier_ymlu import CarrierYmluSpider, MainInfoRoutingRule
from test.spiders.carrier_ymlu import main_info
from test.spiders.utils import extract_url_from


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=main_info, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,mbl_no,', [
    ('01_all_exist', 'W209131160'),
    ('02_no_last_free_day_table', 'W202119769'),
    ('03_no_firms_code', 'W202119210'),
    ('04_no_carrier_and_customs_status', 'E491301617'),
    ('06_no_release', 'I209365239'),
    ('07_multi_containers', 'W241061370'),
    ('08_different_title_on_routing_schedule', 'W125326102'),
])
def test_main_info_routing_rule(sub, mbl_no, sample_loader):
    httptext = sample_loader.read_file(sub, 'sample.html')

    routing_request = MainInfoRoutingRule.build_routing_request(mbl_no=mbl_no)
    url = extract_url_from(routing_request=routing_request)

    response = TextResponse(
        url=url,
        body=httptext,
        encoding='utf-8',
        request=Request(
            url=url,
            meta={
                RuleManager.META_CARRIER_CORE_RULE_NAME: MainInfoRoutingRule.name,
            }
        )
    )

    spider = CarrierYmluSpider(mbl_no=mbl_no)
    results = list(spider.parse(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)


@pytest.mark.parametrize('sub,mbl_no,expect_exception', [
    ('05_invalid_mbl_no', 'W216098981', CarrierInvalidMblNoError),
])
def test_main_info_handler_mbl_no_error(sub, mbl_no, expect_exception, sample_loader):
    httptext = sample_loader.read_file(sub, 'sample.html')

    routing_request = MainInfoRoutingRule.build_routing_request(mbl_no=mbl_no)
    url = extract_url_from(routing_request=routing_request)

    response = TextResponse(
        url=url,
        body=httptext,
        encoding='utf-8',
        request=Request(
            url=url,
            meta={
                RuleManager.META_CARRIER_CORE_RULE_NAME: MainInfoRoutingRule.name,
            }
        )
    )

    spider = CarrierYmluSpider(mbl_no=mbl_no)
    with pytest.raises(expect_exception):
        list(spider.parse(response=response))
