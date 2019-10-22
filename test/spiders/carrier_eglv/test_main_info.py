from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_carrier.exceptions import CarrierInvalidMblNoError
from crawler.core_carrier.rules import RuleManager
from crawler.spiders.carrier_eglv import CarrierEglvSpider, MainInfoRoutingRule, CarrierCaptchaMaxRetryError
from test.spiders.carrier_eglv import samples_main_info


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent / 'samples_main_info'
    sample_loader.setup(sample_package=samples_main_info, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,mbl_no,', [
    ('01_3_containers_not_arrive', '003902245109'),
    ('02_2_containers_arrived', '003901793951'),
    ('05_different_vessel_voyage', '142901393381')
])
def test_main_info_handler(sub, mbl_no, sample_loader):
    main_html_file = str(sample_loader.build_file_path(sub, 'sample.html'))
    with open(main_html_file, 'r', encoding='utf-8') as fp:
        httptext = fp.read()

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

    spider = CarrierEglvSpider(mbl_no=mbl_no)
    results = list(spider.parse(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verifier = verify_module.Verifier()
    verifier.verify(results=results)


@pytest.mark.parametrize('sub,mbl_no,expect_exception', [
    ('03_invalid_mbl_no', '003901796617', CarrierInvalidMblNoError),
])
def test_main_info_handler_mbl_no_error(sub, mbl_no, expect_exception, sample_loader):
    main_html_file = str(sample_loader.build_file_path(sub, 'sample.html'))
    with open(main_html_file, 'r', encoding='utf-8') as fp:
        httptext = fp.read()

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

    spider = CarrierEglvSpider(mbl_no=mbl_no)
    with pytest.raises(expect_exception):
        list(spider.parse(response=response))


@pytest.mark.parametrize('sub,mbl_no,expect_exception', [
    ('04_invalid_captcha_max_retry', '', CarrierCaptchaMaxRetryError),
])
def test_main_info_handler_max_retry_error(sub, mbl_no, expect_exception, sample_loader):
    html_file = str(sample_loader.build_file_path(sub, 'sample.html'))
    with open(html_file, 'r', encoding='utf-8') as fp:
        html_text = fp.read()

    response = TextResponse(
        url='https://www.shipmentlink.com/servlet/TDB1_CargoTracking.do',
        body=html_text,
        encoding='utf-8',
        request=Request(
            url='https://www.shipmentlink.com/servlet/TDB1_CargoTracking.do',
            meta={
                RuleManager.META_CARRIER_CORE_RULE_NAME: MainInfoRoutingRule.name,
                'mbl_no': mbl_no,
            }
        )
    )

    spider = CarrierEglvSpider(mbl_no=mbl_no)

    for i in range(3):
        list(spider.parse(response=response))
    with pytest.raises(expect_exception):  # The forth retry
        list(spider.parse(response=response))

