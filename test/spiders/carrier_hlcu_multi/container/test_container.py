from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse
from scrapy.selector import Selector

from crawler.spiders.carrier_hlcu_multi import TracingRoutingRule
from test.spiders.carrier_hlcu_multi import container


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=container, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    "sub,mbl_no,container_no",
    [
        ("01_finish", "HLCUSHA1904CCVX4", "HLBU2060615"),
        ("02_not_finish", "HLCUSHA1911AVPN9", "UACU5837527"),
        ("03_without_time", "HLCULGB191208765", "TCLU7285161"),
    ],
)
def test_container_handler(sub, mbl_no, container_no, sample_loader):
    http_text = sample_loader.read_file(sub, "sample.html")

    rule = TracingRoutingRule(content_getter=None)
    results = list(rule._handle_container(page=http_text, container_no=container_no, task_id=1))

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verifier = verify_module.Verifier()
    verifier.verify(results=results)
