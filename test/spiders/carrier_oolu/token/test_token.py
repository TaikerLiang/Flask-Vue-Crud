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


@pytest.mark.parametrize('sub,jsession_cookie,mbl_no', [
    (
            '01',
            b'JSESSIONID=n8XBQ52UdPTKMYF_v9Y847OP0R9jTvdgdpOa-_ySJ-0AssuZ6yAf!1368327407; path=/party; HttpOnly',
            '2634031060',
    ),
])
def test_token_handler(sub, jsession_cookie, mbl_no, sample_loader):
    html_file = sample_loader.read_file(sub, 'sample.html')

    option = TokenRoutingRule.build_request_option(mbl_no=mbl_no, cookie_jar_id=0)
    response = TextResponse(
        url=option.url,
        body=html_file,
        headers={
            'Set-Cookie': [
                jsession_cookie,
            ]
        },
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

