from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_carrier.rules import RuleManager
from crawler.spiders.carrier_oolu import TokenRoutingRule
from test.spiders.carrier_oolu import token


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=token, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,mbl_no', [
    ('01', '2634031060'),
])
def test_token_handler(sub, mbl_no, sample_loader):
    html_file = sample_loader.read_file(sub, 'sample.html')

    url = (
        f'http://moc.oocl.com/party/cargotracking/ct_search_from_other_domain.jsf?ANONYMOUS_BEHAVIOR=BUILD_UP&'
        f'domainName=PARTY_DOMAIN&ENTRY_TYPE=OOCL&ENTRY=MCC&ctSearchType=BL&ctShipmentNumber={mbl_no}'
    )
    response = TextResponse(
        url=url,
        body=html_file,
        encoding='utf-8',
        request=Request(
            url=url,
            meta={
                RuleManager.META_CARRIER_CORE_RULE_NAME: TokenRoutingRule.name,
                'mbl_no': mbl_no,
            }
        )
    )

    rule = TokenRoutingRule()
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)

