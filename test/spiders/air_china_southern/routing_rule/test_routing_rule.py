from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.spiders.air_china_southern import AirInfoRoutingRule
from test.spiders.air_china_southern import routing_rule


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=routing_rule, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    "sub, task_id, mawb_no",
    [
        ("01_basic", "1", "66323191"),
        ("02_data_not_found", "1", "46449060"),
    ],
)
def test_routing_rule_handle(sub, task_id, mawb_no, sample_loader):
    http_text = sample_loader.read_file(sub, "sample.html")

    option = AirInfoRoutingRule.build_request_option(task_id=task_id, mawb_no=mawb_no)

    response = TextResponse(
        url=option.url,
        body=http_text,
        encoding="utf-8",
        request=Request(
            url=option.url,
            meta=option.meta,
        ),
    )

    rule = AirInfoRoutingRule()
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verify_module.verify(results=results)
