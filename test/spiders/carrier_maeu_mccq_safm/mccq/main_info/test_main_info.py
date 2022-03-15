from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_carrier.base import SHIPMENT_TYPE_MBL
from crawler.core_carrier.exceptions import CarrierInvalidSearchNoError
from crawler.core_carrier.maeu_mccq_safm_share_spider import MainInfoRoutingRule
from crawler.core_carrier.request_helpers import RequestOption
from crawler.spiders.carrier_mccq import CarrierMccqSpider
from test.spiders.carrier_maeu_mccq_safm.mccq import main_info


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=main_info, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    "sub,mbl_no,",
    [
        ("01_multi_containers_finish", "589898475"),
        ("02_multi_containers_not_finish", "588455529"),
    ],
)
def test_main_info_routing_rule(sub, mbl_no, sample_loader):
    jsontext = sample_loader.read_file(sub, "sample.json")

    option = MainInfoRoutingRule.build_request_option(search_no=mbl_no, url_format=CarrierMccqSpider.base_url_format)

    response = TextResponse(
        url=option.url,
        body=jsontext,
        encoding="utf-8",
        request=Request(
            url=option.url,
        ),
    )

    routing_rule = MainInfoRoutingRule(search_type=SHIPMENT_TYPE_MBL)
    results = list(routing_rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verify_module.verify(results=results)


@pytest.mark.parametrize(
    "sub,mbl_no,expect_exception",
    [
        ("e01_invalid_mbl_no", "999455999", CarrierInvalidSearchNoError),
    ],
)
def test_main_info_handler_mbl_no_error(sub, mbl_no, expect_exception, sample_loader):
    jsontext = sample_loader.read_file(sub, "sample.json")

    option = MainInfoRoutingRule.build_request_option(search_no=mbl_no, url_format=CarrierMccqSpider.base_url_format)

    response = TextResponse(
        url=option.url,
        body=jsontext,
        encoding="utf-8",
        request=Request(
            url=option.url,
        ),
    )

    routing_rule = MainInfoRoutingRule(search_type=SHIPMENT_TYPE_MBL)

    with pytest.raises(expect_exception):
        list(routing_rule.handle(response=response))


@pytest.mark.parametrize(
    "mbl_no,",
    [
        ("SEAU216572195"),
    ],
)
def test_build_special_request_option(mbl_no):
    # arrange
    expect_option = RequestOption(
        method=RequestOption.METHOD_GET,
        rule_name="MAIN_INFO",
        url=f"https://api.maerskline.com/track/{mbl_no[4:]}?operator=seau",
        meta={
            "handle_httpstatus_list": [400, 404],
        },
    )

    # action
    option = MainInfoRoutingRule.build_request_option(search_no=mbl_no, url_format=CarrierMccqSpider.base_url_format)

    # assertion
    assert option == expect_option
