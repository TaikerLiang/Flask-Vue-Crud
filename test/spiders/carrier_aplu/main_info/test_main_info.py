from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_carrier.base import SHIPMENT_TYPE_MBL
from crawler.core_carrier.exceptions import CarrierInvalidMblNoError, CarrierInvalidSearchNoError
from crawler.spiders.carrier_anlc_aplu_cmdu import CarrierApluSpider, FirstTierRoutingRule
from test.spiders.carrier_aplu import main_info


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=main_info, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    'sub,mbl_no',
    [
        ('01_not_finish', 'AXK0185154'),
        ('02_finish', 'XHMN810789'),
        ('03_multiple_containers', 'SHSE015942'),
        ('04_por_dest', 'AWB0135426'),
        ('05_pod_status_is_remaining', 'NANZ001007'),
        ('06_container_status_has_extra_tr', 'AYU0320031'),
    ],
)
def test_first_tier_routing_rule(sample_loader, sub, mbl_no):
    html_text = sample_loader.read_file(sub, 'main_info.html')

    option = FirstTierRoutingRule.build_request_option(
        search_no=mbl_no, base_url=CarrierApluSpider.base_url, search_type=SHIPMENT_TYPE_MBL)

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
    ('e01_invalid_mbl_no', 'XHMN810788', CarrierInvalidSearchNoError),
])
def test_first_tier_routing_rule_error(sample_loader, sub, mbl_no, expect_exception):
    html_text = sample_loader.read_file(sub, 'main_info.html')

    option = FirstTierRoutingRule.build_request_option(
        search_no=mbl_no, base_url=CarrierApluSpider.base_url, search_type=SHIPMENT_TYPE_MBL)

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
