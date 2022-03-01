from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core.base import SEARCH_TYPE_BOOKING
from crawler.spiders.carrier_eglv_multi import BookingMainInfoRoutingRule
from test.spiders.carrier_eglv_multi import booking_main_info


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=booking_main_info, sample_path=sample_path)
    return sample_loader


# @pytest.mark.parametrize(
#     "sub,booking_no,",
#     [
#         ("01_basic", "110381781"),
#     ],
# )
# def test_main_info_handler(sub, booking_no, sample_loader):
#     httptext = sample_loader.read_file(sub, "sample.html")

#     option = BookingMainInfoRoutingRule.build_request_option(
#         search_nos=[booking_no], verification_code="", task_ids=["1"],
#     )

#     response = TextResponse(
#         url=option.url,
#         body=httptext,
#         encoding="utf-8",
#         request=Request(url=option.url, meta=option.meta),
#     )

#     rule = BookingMainInfoRoutingRule(content_getter=None)
#     results = list(rule.handle(response=response))

#     verify_module = sample_loader.load_sample_module(sub, "verify")
#     verifier = verify_module.Verifier()
#     verifier.verify(results=results)


@pytest.mark.parametrize(
    "sub,booking_no,",
    [
        ("01_basic", "110381781"),
    ],
)
def test_extract_booking_no_and_vessel_voyage(sub, booking_no, sample_loader):
    httptext = sample_loader.read_file(sub, "sample.html")

    option = BookingMainInfoRoutingRule.build_request_option(
        search_nos=[booking_no],
        verification_code="",
        task_ids=["1"],
    )

    response = TextResponse(
        url=option.url,
        body=httptext,
        encoding="utf-8",
        request=Request(url=option.url, meta=option.meta),
    )

    info_pack = {
        "task_id": "1",
        "search_no": booking_no,
        "search_type": SEARCH_TYPE_BOOKING,
    }
    rule = BookingMainInfoRoutingRule(content_getter=None)
    results = rule._extract_booking_no_and_vessel_voyage(response=response, info_pack=info_pack)

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verifier = verify_module.Verifier()
    verifier.verify_booking_no_and_vessel_voyage(results=results)


@pytest.mark.parametrize(
    "sub,booking_no,",
    [
        ("01_basic", "110381781"),
    ],
)
def test_extract_basic_info(sub, booking_no, sample_loader):
    httptext = sample_loader.read_file(sub, "sample.html")

    option = BookingMainInfoRoutingRule.build_request_option(
        search_nos=[booking_no],
        verification_code="",
        task_ids=["1"],
    )

    response = TextResponse(
        url=option.url,
        body=httptext,
        encoding="utf-8",
        request=Request(url=option.url, meta=option.meta),
    )

    rule = BookingMainInfoRoutingRule(content_getter=None)
    results = rule._extract_basic_info(response=response)

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verifier = verify_module.Verifier()
    verifier.verify_basic(results=results)


@pytest.mark.parametrize(
    "sub,booking_no,",
    [
        ("01_basic", "110381781"),
    ],
)
def test_extract_filing_info(sub, booking_no, sample_loader):
    httptext = sample_loader.read_file(sub, "sample.html")

    option = BookingMainInfoRoutingRule.build_request_option(
        search_nos=[booking_no],
        verification_code="",
        task_ids=["1"],
    )

    response = TextResponse(
        url=option.url,
        body=httptext,
        encoding="utf-8",
        request=Request(url=option.url, meta=option.meta),
    )

    rule = BookingMainInfoRoutingRule(content_getter=None)
    results = rule._extract_filing_info(response=response)

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verifier = verify_module.Verifier()
    verifier.verify_filing_info(results=results)


@pytest.mark.parametrize(
    "sub,booking_no,",
    [
        ("01_basic", "110381781"),
    ],
)
def test_extract_container_infos(sub, booking_no, sample_loader):
    httptext = sample_loader.read_file(sub, "sample.html")

    option = BookingMainInfoRoutingRule.build_request_option(
        search_nos=[booking_no],
        verification_code="",
        task_ids=["1"],
    )

    response = TextResponse(
        url=option.url,
        body=httptext,
        encoding="utf-8",
        request=Request(url=option.url, meta=option.meta),
    )

    rule = BookingMainInfoRoutingRule(content_getter=None)
    results = rule._extract_container_infos(response=response)

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verifier = verify_module.Verifier()
    verifier.verify_container_infos(results=results)
