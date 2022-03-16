from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.spiders.air_china_southern import PREFIX, AirInfoRoutingRule
from test.spiders.air_china_southern import routing_rule


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=routing_rule, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    "sub, mawb_no",
    [
        ("01_basic", "66323191"),
        ("02_data_not_found", "46449060"),
    ],
)
def test_routing_rule_handle(sub, mawb_no, sample_loader):
    http_text = sample_loader.read_file(sub, "sample.html")

    url = (
        f"https://tang.csair.com/EN/WebFace/Tang.WebFace.Cargo/AgentAwbBrower.aspx?"
        f"awbprefix={PREFIX}&awbno={mawb_no}&lan=en-us"
    )
    response = TextResponse(
        url=url,
        body=http_text,
        encoding="utf-8",
        request=Request(
            url=url,
            meta={"search_no": mawb_no, "task_id": "1"},
        ),
    )

    rule = AirInfoRoutingRule()
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verify_module.verify(results=results)
