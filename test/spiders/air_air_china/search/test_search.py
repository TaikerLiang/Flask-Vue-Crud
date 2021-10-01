from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.spiders.air_air_china import SearchRoutingRule
from test.spiders.air_air_china import search


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=search, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    "sub, mawb_no, task_id",
    [
        ("01_basic", "14426156", "1"),
        ("02_data_not_found", "16830165", "2"),
    ],
)
def test_search_handle(sub, mawb_no, task_id, sample_loader):
    httptext = sample_loader.read_file(sub, "sample.html")

    url = "https://www.airchinacargo.com/en/search_order.php"
    response = TextResponse(
        url=url,
        body=httptext,
        encoding="utf-8",
        request=Request(
            url=url,
            meta={
                "mawb_no": mawb_no,
                "task_id": task_id,
            },
        ),
    )

    rule = SearchRoutingRule()
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, "verify")
    verify_module.verify(results=results)
