from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.spiders.carrier_oolu import ChallengeRoutingRule
from test.spiders.carrier_oolu import challenge


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=challenge, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,mbl_no', [
    ('01_basic', '2644145880'),
])
def test_cookies_handler(sub, mbl_no, sample_loader):
    http_text = sample_loader.read_file(sub, 'sample.html')

    option = ChallengeRoutingRule.build_request_option(mbl_no=mbl_no)
    response = TextResponse(
        url=option.url,
        body=http_text,
        encoding='utf-8',
        request=Request(
            url=option.url,
            meta=option.meta,
        )
    )

    rule = ChallengeRoutingRule()
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)

