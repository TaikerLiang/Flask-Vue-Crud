from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.spiders.air_eva import DetailPageRoutingRule
from test.spiders.air_eva import detail_page


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=detail_page, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    'sub,mawb_no',
    [
        ('01_basic', '28809955'),
    ],
)
def test_detail_page_handle(sub, mawb_no, sample_loader):
    json_text = sample_loader.read_file(sub, 'DETAIL_PAGE.html')

    option = DetailPageRoutingRule.build_request_option(mawb_no=mawb_no)

    response = TextResponse(
        url=option.url,
        body=json_text,
        encoding='utf-8',
        request=Request(
            url=option.url,
            meta=option.meta,
        ),
    )

    routing_rule = DetailPageRoutingRule()
    results = list(routing_rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)

