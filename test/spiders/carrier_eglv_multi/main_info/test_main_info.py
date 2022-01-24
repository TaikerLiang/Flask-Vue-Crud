from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.spiders.carrier_eglv_multi import BillMainInfoRoutingRule
from test.spiders.carrier_eglv_multi import main_info


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=main_info, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    "sub,mbl_no,",
    [
        ("01_3_containers_not_arrive", "003902245109"),
        ("02_2_containers_arrived", "003901793951"),
        ("03_different_vessel_voyage", "142901393381"),
        ("04_without_filing_status", "100980089898"),
        ("05_without_container_info_table", "003903689108"),
    ],
)
def test_hidden_info(sub, mbl_no, sample_loader):
    httptext = sample_loader.read_file(sub, "sample.html")

    option = BillMainInfoRoutingRule.build_request_option(
        search_nos=[mbl_no],
        verification_code="",
        task_ids=["1"],
    )

    response = TextResponse(
        url=option.url,
        body=httptext,
        encoding="utf-8",
        request=Request(url=option.url, meta=option.meta),
    )

    rule = BillMainInfoRoutingRule(content_getter=None)
    results = rule._extract_hidden_info(response=response)

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verifier = verify_module.Verifier()
    verifier.verify_hidden_info(results=results)


@pytest.mark.parametrize(
    "sub,mbl_no,",
    [
        ("01_3_containers_not_arrive", "003902245109"),
        ("02_2_containers_arrived", "003901793951"),
        ("03_different_vessel_voyage", "142901393381"),
        ("04_without_filing_status", "100980089898"),
        ("05_without_container_info_table", "003903689108"),
    ],
)
def test_basic_info(sub, mbl_no, sample_loader):
    httptext = sample_loader.read_file(sub, "sample.html")

    option = BillMainInfoRoutingRule.build_request_option(
        search_nos=[mbl_no],
        verification_code="",
        task_ids=["1"],
    )

    response = TextResponse(
        url=option.url,
        body=httptext,
        encoding="utf-8",
        request=Request(url=option.url, meta=option.meta),
    )

    rule = BillMainInfoRoutingRule(content_getter=None)
    results = rule._extract_basic_info(response=response)

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verifier = verify_module.Verifier()
    verifier.verify_basic_info(results=results)


@pytest.mark.parametrize(
    "sub,mbl_no,pod",
    [
        ("01_3_containers_not_arrive", "003902245109", "BOSTON, MA (US)"),
        ("02_2_containers_arrived", "003901793951", "BALTIMORE, MD (US)"),
        ("03_different_vessel_voyage", "142901393381", "LONG BEACH, CA (US)"),
        ("04_without_filing_status", "100980089898", "LOS ANGELES, CA (US)"),
        ("05_without_container_info_table", "003903689108", "BOSTON, MA (US)"),
    ],
)
def test_vessel_info(sub, mbl_no, pod, sample_loader):
    httptext = sample_loader.read_file(sub, "sample.html")

    option = BillMainInfoRoutingRule.build_request_option(
        search_nos=[mbl_no],
        verification_code="",
        task_ids=["1"],
    )

    response = TextResponse(
        url=option.url,
        body=httptext,
        encoding="utf-8",
        request=Request(url=option.url, meta=option.meta),
    )

    rule = BillMainInfoRoutingRule(content_getter=None)
    results = rule._extract_vessel_info(response=response, pod=pod)

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verifier = verify_module.Verifier()
    verifier.verify_vessel_info(results=results)


# @pytest.mark.parametrize(
#     "sub,mbl_no,expect_exception",
#     [
#         ("e01_invalid_captcha_max_retry", "", CarrierCaptchaMaxRetryError),
#     ],
# )
# def test_main_info_handler_max_retry_error(sub, mbl_no, expect_exception, sample_loader):
#     httptext = sample_loader.read_file(sub, "sample.html")
#
#     option = BillMainInfoRoutingRule.build_request_option(mbl_nos=[mbl_no], verification_code="", task_ids=["1"], search_type=SHIPMENT_TYPE_MBL)
#
#     response = TextResponse(
#         url=option.url,
#         body=httptext,
#         encoding="utf-8",
#         request=Request(url=option.url, meta=option.meta),
#     )
#
#     rule = BillMainInfoRoutingRule()
#
#     for i in range(3):
#         list(rule.handle(response=response))
#     with pytest.raises(expect_exception):  # The forth retry
#         list(rule.handle(response=response))
