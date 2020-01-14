from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_carrier.exceptions import CarrierInvalidMblNoError
from crawler.core_carrier.rules import RuleManager
from crawler.spiders.carrier_eglv import MainInfoRoutingRule, CarrierCaptchaMaxRetryError
from test.spiders.carrier_eglv import main_info


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=main_info, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,mbl_no,', [
    ('01_3_containers_not_arrive', '003902245109'),
    ('02_2_containers_arrived', '003901793951'),
    ('03_different_vessel_voyage', '142901393381'),
    ('04_without_filing_status', '100980089898'),
    ('05_without_container_info_table', '003903689108'),
])
def test_main_info_handler(sub, mbl_no, sample_loader):
    httptext = sample_loader.read_file(sub, 'sample.html')

    response = TextResponse(
        url='https://www.shipmentlink.com/servlet/TDB1_CargoTracking.do',
        body=httptext,
        encoding='utf-8',
        request=Request(
            url='https://www.shipmentlink.com/servlet/TDB1_CargoTracking.do',
            meta={
                'mbl_no': mbl_no,
            }
        )
    )

    rule = MainInfoRoutingRule()
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verifier = verify_module.Verifier()
    verifier.verify(results=results)


@pytest.mark.parametrize('sub,mbl_no,expect_exception', [
    ('e01_invalid_mbl_no', '003901796617', CarrierInvalidMblNoError),
    ('e03_invalid_mbl_no_format', '0039030726400', CarrierInvalidMblNoError),
])
def test_main_info_handler_mbl_no_error(sub, mbl_no, expect_exception, sample_loader):
    httptext = sample_loader.read_file(sub, 'sample.html')

    response = TextResponse(
        url='https://www.shipmentlink.com/servlet/TDB1_CargoTracking.do',
        body=httptext,
        encoding='utf-8',
        request=Request(
            url='https://www.shipmentlink.com/servlet/TDB1_CargoTracking.do',
            meta={
                RuleManager.META_CARRIER_CORE_RULE_NAME: MainInfoRoutingRule.name,
                'mbl_no': mbl_no,
            }
        )
    )

    rule = MainInfoRoutingRule()
    with pytest.raises(expect_exception):
        list(rule.handle(response=response))


@pytest.mark.parametrize('sub,mbl_no,expect_exception', [
    ('e02_invalid_captcha_max_retry', '', CarrierCaptchaMaxRetryError),
])
def test_main_info_handler_max_retry_error(sub, mbl_no, expect_exception, sample_loader):
    httptext = sample_loader.read_file(sub, 'sample.html')

    response = TextResponse(
        url='https://www.shipmentlink.com/servlet/TDB1_CargoTracking.do',
        body=httptext,
        encoding='utf-8',
        request=Request(
            url='https://www.shipmentlink.com/servlet/TDB1_CargoTracking.do',
            meta={
                'mbl_no': mbl_no,
            }
        )
    )

    rule = MainInfoRoutingRule()

    for i in range(3):
        list(rule.handle(response=response))
    with pytest.raises(expect_exception):  # The forth retry
        list(rule.handle(response=response))
