from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_carrier.rules import RuleManager
from crawler.core_carrier.exceptions import CarrierInvalidMblNoError
from crawler.spiders.carrier_oolu import CargoTrackingRule
from test.spiders.carrier_oolu import cargo_tracking


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=cargo_tracking, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,mbl_no', [
    ('01_single_container', '2625845270'),
    ('02_multi_containers', '2109051600'),
    ('03_without_custom_release_date', '2628633440'),
    ('04_tranship_exist', '2630699272'),
])
def test_cargo_tracking_handler(sub, mbl_no, sample_loader):
    html_file = sample_loader.read_file(sub, 'sample.html')

    url = (
        'http://moc.oocl.com/party/cargotracking/ct_search_from_other_domain.jsf?'
        'ANONYMOUS_TOKEN=kFiFirZYfIHjjEVjGlDTMCCOOCL&ENTRY_TYPE=OOCL'
    )
    response = TextResponse(
        url=url,
        body=html_file,
        encoding='utf-8',
        request=Request(
            url=url,
            meta={
                RuleManager.META_CARRIER_CORE_RULE_NAME: CargoTrackingRule.name,
                'mbl_no': mbl_no,
            }
        )
    )

    rule = CargoTrackingRule()
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)


@pytest.mark.parametrize('sub,mbl_no,expect_exception', [
    ('e01_invalid_mbl_no', 'OOLU0000000000', CarrierInvalidMblNoError),
])
def test_cargo_tracking_handler_no_mbl_error(sub, mbl_no, expect_exception, sample_loader):
    html_file = sample_loader.read_file(sub, 'sample.html')

    url = (
        'http://moc.oocl.com/party/cargotracking/ct_search_from_other_domain.jsf?'
        'ANONYMOUS_TOKEN=kFiFirZYfIHjjEVjGlDTMCCOOCL&ENTRY_TYPE=OOCL'
    )
    response = TextResponse(
        url=url,
        body=html_file,
        encoding='utf-8',
        request=Request(
            url=url,
            meta={
                RuleManager.META_CARRIER_CORE_RULE_NAME: CargoTrackingRule.name,
                'mbl_no': mbl_no,
            }
        )
    )

    rule = CargoTrackingRule()
    with pytest.raises(expect_exception):
        list(rule.handle(response=response))
