from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core.base import SEARCH_TYPE_MBL
from crawler.spiders.carrier_mscu_multi import MainRoutingRule
from test.spiders.carrier_mscu_multi import main_info


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=main_info, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    "sub,mbl_no,",
    [
        ("01_without_ts_port", "MEDUN4194175"),
        ("02_not_arrival_yet", "MEDUNG283959"),
        ("03_multi_containers", "MEDUMY898253"),
        ("04_data_not_found", "MEDUMY898252"),
    ],
)
def test_main_info_routing_rule(sub, mbl_no, sample_loader):
    http_text = sample_loader.read_file(sub, "sample.html")

    url = "https://www.msc.com/track-a-shipment?agencyPath=twn"
    response = TextResponse(
        url=url,
        body=http_text,
        encoding="utf-8",
        request=Request(
            url=url,
            meta={
                "search_nos": [mbl_no],
                "task_ids": ["1"],
            },
        ),
    )

    rule = MainRoutingRule(search_type=SEARCH_TYPE_MBL)
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verify_module.verify(results=results)
