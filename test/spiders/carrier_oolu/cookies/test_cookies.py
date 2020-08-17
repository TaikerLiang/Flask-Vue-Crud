from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.spiders.carrier_oolu import CookiesRoutingRule
from test.spiders.carrier_oolu import cookies


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=cookies, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,bot_cookie,mbl_no', [
    (
            '01',
            b'BotMitigationCookie_2943835814907568976="729842001597658914F7dOuumI8IjGcpgPUi6SOcUc2Do="; path=/',
            '2634031060',
    ),
])
def test_cookies_handler(sub, bot_cookie, mbl_no, sample_loader):

    option = CookiesRoutingRule.build_request_option(mbl_no=mbl_no, challenge='', challenge_id='', challenge_result='')
    response = TextResponse(
        url=option.url,
        body='',
        headers={
            'Set-Cookie': [
                bot_cookie,
            ]
        },
        encoding='utf-8',
        request=Request(
            url=option.url,
            meta=option.meta,
        )
    )

    rule = CookiesRoutingRule()
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)

