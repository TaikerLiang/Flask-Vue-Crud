from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core.base import SEARCH_TYPE_MBL
from crawler.core.exceptions import GeneralError
from crawler.spiders.carrier_zimu import MainInfoRoutingRule
from test.spiders.carrier_zimu import main_info


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=main_info, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    "sub,mbl_no,",
    [
        ("01_only_pod_in_schedule", "ZIMUSNH1160339"),
        ("02_multi_ships", "ZIMUNGB9355973"),
        ("03_second_ship_not_show", "ZIMUNGB9490976"),
        ("04_without_ts_port", "ZIMULAX0139127"),
        ("05_final_dest_not_un_lo_code", "ZIMUSNH1105927"),
        ("06_pol_in_routing_schedule", "ZIMULAX0140902"),
        ("07_routing_schedule_without_arrival_date", "ZIMUORF0941773"),
        ("08_routing_schedule_without_sailing_date", "ZIMUNGB9491892"),
    ],
)
def test_main_info_handle(sub, mbl_no, sample_loader):
    info_pack = {
        "task_id": "1",
        "search_no": mbl_no,
        "search_type": SEARCH_TYPE_MBL,
    }

    httptext = sample_loader.read_file(sub, "sample.html")
    option = MainInfoRoutingRule.build_request_option(task_id=info_pack["task_id"], mbl_no=info_pack["search_no"])
    response = TextResponse(
        url=option.url,
        body=httptext,
        encoding="utf-8",
        request=Request(
            url=option.url,
            meta=option.meta,
        ),
    )

    rule = MainInfoRoutingRule()
    results = list(rule._handle_item(response=response, info_pack=info_pack))

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verify_module.verify(results=results)


@pytest.mark.parametrize(
    "sub,mbl_no",
    [
        ("e01_invalid_mbl_no", "ZIMUSNH110567"),
    ],
)
def test_main_info_handler_is_not_found(sub, mbl_no, sample_loader):
    httptext = sample_loader.read_file(sub, "sample.html")

    option = MainInfoRoutingRule.build_request_option(task_id="1", mbl_no=mbl_no)

    response = TextResponse(
        url=option.url,
        body=httptext,
        encoding="utf-8",
        request=Request(
            url=option.url,
            meta=option.meta,
        ),
    )

    rule = MainInfoRoutingRule()
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verify_module.verify(results=results)


@pytest.mark.parametrize(
    "sub,mbl_no,expect_exception",
    [
        ("e02_invalid_mbl_no_format", "ZIMUORF0946735/1", GeneralError),
    ],
)
def test_main_info_handler_is_mbl_no_format_error(sub, mbl_no, expect_exception, sample_loader):
    httptext = sample_loader.read_file(sub, "sample.html")

    option = MainInfoRoutingRule.build_request_option(task_id="1", mbl_no=mbl_no)

    response = TextResponse(
        url=option.url,
        body=httptext,
        encoding="utf-8",
        request=Request(
            url=option.url,
            meta=option.meta,
        ),
    )

    rule = MainInfoRoutingRule()
    with pytest.raises(expect_exception):
        list(rule.handle(response=response))
