from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_carrier.base import SHIPMENT_TYPE_MBL
from crawler.core_carrier.exceptions import CarrierInvalidMblNoError, CarrierInvalidSearchNoError
from crawler.spiders.carrier_anlc_aplu_cmdu import CarrierAnlcSpider, FirstTierRoutingRule
from test.spiders.carrier_anlc import main_info


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=main_info, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    'sub,mbl_no',
    [
        ('01_not_finish', 'AWT0143054'),
        ('02_finish', 'AWT0143291'),
        ('03_multiple_containers', 'AWT0143454'),
        ('04_pod_status_is_remaining', 'AWT0143370'),
    ],
)
def test_first_tier_routing_rule(sample_loader, sub, mbl_no):
    html_text = sample_loader.read_file(sub, 'main_info.html')

    option = FirstTierRoutingRule.build_request_option(
        base_url=CarrierAnlcSpider.base_url, search_no=mbl_no, search_type=SHIPMENT_TYPE_MBL)

    response = TextResponse(
        url=option.url,
        encoding='utf-8',
        body=html_text,
        request=Request(
            url=option.url,
            meta=option.meta,
        )
    )

    routing_rule = FirstTierRoutingRule(search_type=SHIPMENT_TYPE_MBL)
    results = list(routing_rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)


@pytest.mark.parametrize('sub,mbl_no,expect_exception', [
    ('e01_invalid_mbl_no', 'AWT0143111', CarrierInvalidSearchNoError),
])
def test_first_tier_routing_rule_error(sample_loader, sub, mbl_no, expect_exception):
    html_text = sample_loader.read_file(sub, 'main_info.html')

    option = FirstTierRoutingRule.build_request_option(
        base_url=CarrierAnlcSpider.base_url, search_no=mbl_no, search_type=SHIPMENT_TYPE_MBL)

    response = TextResponse(
        url=option.url,
        encoding='utf-8',
        body=html_text,
        request=Request(
            url=option.url,
            meta=option.meta,
        ),
    )
    routing_rule = FirstTierRoutingRule(search_type=SHIPMENT_TYPE_MBL)
    with pytest.raises(expect_exception):
        list(routing_rule.handle(response=response))
