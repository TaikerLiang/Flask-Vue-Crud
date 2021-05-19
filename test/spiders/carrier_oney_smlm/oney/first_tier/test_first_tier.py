from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_carrier.exceptions import CarrierInvalidMblNoError
from crawler.spiders.carrier_oney_smlm import FirstTierRoutingRule, CarrierOneySpider
from test.spiders.carrier_oney_smlm.oney import first_tier


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=first_tier, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    'sub,mbl_no,base_url',
    [
        ('01_single_container', 'SH9FSK690300', CarrierOneySpider.base_url),
        ('02_multiple_containers', 'SZPVF2740514', CarrierOneySpider.base_url),
    ],
)
def test_first_tier_handle(sub, mbl_no, base_url, sample_loader):
    jsontext = sample_loader.read_file(sub, 'sample.json')

    option = FirstTierRoutingRule.build_request_option(mbl_no=mbl_no, base_url=base_url)

    response = TextResponse(
        url=option.url,
        body=jsontext,
        encoding='utf-8',
        request=Request(
            url=option.url,
        ),
    )

    rule = FirstTierRoutingRule(CarrierOneySpider.base_url)
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)


@pytest.mark.parametrize(
    'sub,mbl_no,expect_exception',
    [
        ('e01_invalid_mbl_no', 'SH9ACBH1540', CarrierInvalidMblNoError),
    ],
)
def test_main_info_handl_mbl_no_error(sub, mbl_no, expect_exception, sample_loader):
    jsontext = sample_loader.read_file(sub, 'sample.json')

    option = FirstTierRoutingRule.build_request_option(mbl_no=mbl_no, base_url=CarrierOneySpider.base_url)

    response = TextResponse(
        url=option.url,
        body=jsontext,
        encoding='utf-8',
        request=Request(
            url=option.url,
        ),
    )

    rule = FirstTierRoutingRule(CarrierOneySpider.base_url)
    with pytest.raises(expect_exception):
        list(rule.handle(response=response))
