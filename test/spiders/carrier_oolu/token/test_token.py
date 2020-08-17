from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.spiders.carrier_oolu import TokenRoutingRule
from test.spiders.carrier_oolu import token


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=token, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,mbl_no', [
    ('01_no_recaptcha', '2634031060'),
    ('02_blocked', '2644690600'),
])
def test_token_handler(sub, mbl_no, sample_loader):
    http_text = sample_loader.read_file(sub, 'sample.html')

    option = TokenRoutingRule.build_request_option(mbl_no=mbl_no)
    response = TextResponse(
        url=option.url,
        body=http_text,
        encoding='utf-8',
        request=Request(
            url=option.url,
            meta=option.meta,
        )
    )

    rule = TokenRoutingRule()
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)

