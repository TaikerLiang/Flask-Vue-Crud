from pathlib import Path
from test.spiders.carrier_mats_multi import main_information

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_carrier.base import SHIPMENT_TYPE_MBL
from crawler.spiders.carrier_mats_multi import MainInfoRoutingRule


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=main_information, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    "sub,mbl_no,",
    [
        ("01_one_container", "1499691000"),
        ("02_multiple_container_with_same_name", "5432696000"),
        ("03_data_not_found", "9069059001"),
    ],
)
def test_main_info_handler(sub, mbl_no, sample_loader):
    json_text = sample_loader.read_file(sub, "main_information.json")

    option = MainInfoRoutingRule.build_request_option(search_no=mbl_no, search_type=SHIPMENT_TYPE_MBL, task_id="1")

    response = TextResponse(
        url=option.url,
        body=json_text,
        encoding="utf-8",
        request=Request(
            url=option.url,
            meta=option.meta,
        ),
    )

    routing_rule = MainInfoRoutingRule(search_type=SHIPMENT_TYPE_MBL)
    results = list(routing_rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verify_module.verify(results=results)
