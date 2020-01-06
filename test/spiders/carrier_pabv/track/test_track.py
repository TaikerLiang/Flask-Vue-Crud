from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_carrier.rules import RuleManager
from crawler.spiders.carrier_pabv import TrackRoutingRule
from test.spiders.carrier_pabv import track
from crawler.core_carrier.exceptions import CarrierInvalidMblNoError, CarrierResponseFormatError


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=track, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,mbl_no,', [
    ('01_NKAI90055900', 'NKAI90055900'),
    ('02_HUPE90310700', 'HUPE90310700'),
])
def test_track_handler(sub, mbl_no, sample_loader):
    json_text = sample_loader.read_file(sub, 'sample.json')

    option = TrackRoutingRule.build_request_option(mbl_no=mbl_no, cookies={})

    response = TextResponse(
        url=option.url,
        body=json_text,
        encoding='utf-8',
        request=Request(
            url=option.url,
            meta={
                RuleManager.META_CARRIER_CORE_RULE_NAME: TrackRoutingRule.name,
                'mbl_no': mbl_no,
                'cookies': {},
            }
        )
    )

    rule = TrackRoutingRule()
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verifier = verify_module.Verifier()
    verifier.verify(results=results)


@pytest.mark.parametrize('sub,mbl_no,sample_file,expect_exception', [
    ('e01_invalid_mbl_no', 'NKAI00000000', 'sample.json', CarrierInvalidMblNoError),
    ('e02_invalid_cookies', 'NKAI90055900', 'sample.html', CarrierResponseFormatError),
])
def test_track_handler_no_mbl_error(sub, mbl_no, sample_file, expect_exception, sample_loader):
    json_text = sample_loader.read_file(sub, sample_file)

    option = TrackRoutingRule.build_request_option(mbl_no=mbl_no, cookies={})

    response = TextResponse(
        url=option.url,
        body=json_text,
        encoding='utf-8',
        request=Request(
            url=option.url,
            meta={
                RuleManager.META_CARRIER_CORE_RULE_NAME: TrackRoutingRule.name,
                'mbl_no': mbl_no,
                'cookies': '',
            }
        )
    )

    rule = TrackRoutingRule()
    with pytest.raises(expect_exception):
        list(rule.handle(response=response))
