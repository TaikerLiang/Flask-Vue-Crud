from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_carrier.base import SHIPMENT_TYPE_MBL
from crawler.core_carrier.exceptions import CarrierInvalidSearchNoError
from crawler.spiders.carrier_oney_smlm import FirstTierRoutingRule, CarrierSmlmSpider
from test.spiders.carrier_oney_smlm.smlm import first_tier


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=first_tier, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,mbl_no,base_url', [
    ('01_single_container', 'SHSM9C747300', CarrierSmlmSpider.base_url),
    ('02_multiple_containers', 'SHFA9A128100', CarrierSmlmSpider.base_url),
])
def test_first_tier_handle(sub, mbl_no, base_url, sample_loader):
    jsontext = sample_loader.read_file(sub, 'sample.json')

    option = FirstTierRoutingRule.build_request_option(search_no=mbl_no, base_url=base_url)

    response = TextResponse(
        url=option.url,
        body=jsontext,
        encoding='utf-8',
        request=Request(
            url=option.url,
            meta=option.meta,
        )
    )

    rule = FirstTierRoutingRule(search_type=SHIPMENT_TYPE_MBL)
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)


@pytest.mark.parametrize('sub,mbl_no,expect_exception', [
    ('e01_invalid_mbl_no', 'SHFA9A128101', CarrierInvalidSearchNoError),
])
def test_first_tier_handle_mbl_no_error(sub, mbl_no, expect_exception, sample_loader):
    jsontext = sample_loader.read_file(sub, 'sample.json')

    option = FirstTierRoutingRule.build_request_option(search_no=mbl_no, base_url=CarrierSmlmSpider.base_url)

    response = TextResponse(
        url=option.url,
        body=jsontext,
        encoding='utf-8',
        request=Request(
            url=option.url,
            meta=option.meta,
        )
    )

    rule = FirstTierRoutingRule(search_type=SHIPMENT_TYPE_MBL)
    with pytest.raises(expect_exception):
        list(rule.handle(response=response))
