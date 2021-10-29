from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_carrier.base import SHIPMENT_TYPE_MBL
from crawler.spiders.carrier_hdmu_multi import ContainerRoutingRule, ItemRecorder
from test.spiders.carrier_hdmu_multi import container


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=container, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    "sub,mbl_no,container_no,container_index",
    [
        ("01_first", "SZPM48676100", "HDMU6660528", 0),
        ("02_without_empty_container_return_location", "DALA80396700", "KOCU4954805", 0),
    ],
)
def test_container_routing_rule(sub, mbl_no, sample_loader, container_no, container_index):
    html_text = sample_loader.read_file(sub, "sample.html")

    option = ContainerRoutingRule.build_request_option(
        search_no=mbl_no,
        task_id="1",
        search_type=SHIPMENT_TYPE_MBL,
        container_index=container_index,
        h_num=0,
        cookies={},
    )

    response = TextResponse(
        url=option.url,
        body=html_text,
        encoding="utf-8",
        request=Request(
            url=option.url,
            meta=option.meta,
        ),
    )

    item_recorder_map = {"1": ItemRecorder()}
    rule = ContainerRoutingRule(item_recorder_map)
    request_options = list(rule.handle(response=response))
    results = request_options + item_recorder_map["1"].items

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verify_module.verify(results=results)
