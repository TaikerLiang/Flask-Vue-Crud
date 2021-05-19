from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.spiders.carrier_whlc import HistoryRoutingRule
from test.spiders.carrier_whlc import history


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=history, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    'sub,mbl_no,container_no',
    [
        ('01_basic', '0349531933', 'DFSU7597714'),
    ],
)
def test_history_routing_rule(sub, mbl_no, sample_loader, container_no):
    html_text = sample_loader.read_file(sub, 'sample.html')

    option = HistoryRoutingRule.build_request_option(
        mbl_no=mbl_no, container_no=container_no, j_idt='', view_state='', cookies={}
    )

    response = TextResponse(
        url=option.url,
        body=html_text,
        encoding='utf-8',
        request=Request(url=option.url, meta={'container_key': container_no}),
    )

    routing_rule = HistoryRoutingRule()
    results = list(routing_rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)
