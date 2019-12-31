from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_carrier.exceptions import CarrierInvalidMblNoError, CarrierResponseFormatError
from crawler.core_carrier.rules import RuleManager
from crawler.spiders.carrier_hdmu import MainRoutingRule, CookiesRoutingRule, CarrierHdmuSpider
from test.spiders.carrier_hdmu import main_info
from test.spiders.utils import extract_url_from


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=main_info, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,mbl_no', [
    ('01_one_container', 'GJWB1899760'),
    ('02_multiple_containers', 'QSWB8011462'),
    ('03_avaliability', 'TAWB0789799'),
    ('04_red_time', 'NXWB1903966'),
    ('05_1_without_lfd', 'QSWB8011632'),
    ('05_2_without_lfd', 'QSWB8011630'),
    ('06_1_original_bl', 'KETC0876470'),
    ('06_2_original_bl', 'QSLB8267628'),
])
def test_parse_main_info(sample_loader, sub, mbl_no):
    html_text = sample_loader.read_file(sub, 'sample.html')

    routing_request = MainRoutingRule.build_routing_request(
        mbl_no=mbl_no, proxy_auth='', callback=CookiesRoutingRule.retry)
    url = extract_url_from(routing_request=routing_request)

    response = TextResponse(
        url=url,
        body=html_text,
        encoding='utf-8',
        request=Request(
            url=url,
            meta={
                RuleManager.META_CARRIER_CORE_RULE_NAME: MainRoutingRule.name,
                'mbl_no': mbl_no,
                'proxy': '',
                'callback': CookiesRoutingRule.retry,
            }
        )
    )

    spider = CarrierHdmuSpider(mbl_no=mbl_no)
    results = list(spider.parse(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)


@pytest.mark.parametrize('sub,mbl_no,expect_exception', [
    ('e01_invalid_mbl', 'QSWB801163', CarrierInvalidMblNoError),
    ('e02_change_header', 'GJWB1899760', CarrierResponseFormatError),
])
def test_parse_main_info_error(sample_loader, sub, mbl_no, expect_exception):
    html_text = sample_loader.read_file(sub, 'sample.html')

    routing_request = MainRoutingRule.build_routing_request(
        mbl_no=mbl_no, proxy_auth='', callback=CookiesRoutingRule.retry)
    url = extract_url_from(routing_request=routing_request)

    response = TextResponse(
        url=url,
        body=html_text,
        encoding='utf-8',
        request=Request(
            url=url,
            meta={
                RuleManager.META_CARRIER_CORE_RULE_NAME: MainRoutingRule.name,
                'mbl_no': mbl_no,
                'proxy': '',
                'callback': CookiesRoutingRule.retry,
            }
        )
    )

    spider = CarrierHdmuSpider(mbl_no=mbl_no)
    with pytest.raises(expect_exception):
        list(spider.parse(response))
