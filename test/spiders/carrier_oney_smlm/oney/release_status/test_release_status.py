from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.spiders.carrier_oney_smlm import CarrierOneySpider, ReleaseStatusRoutingRule
from test.spiders.carrier_oney_smlm.oney import release_status
from test.spiders.utils import extract_url_from


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=release_status, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,mbl_no,cntr_no,bkg_no', [
    ('01', 'SH9FSK690300', 'CLHU9129958', 'SH9FSK690300'),
    ('02_release_info_not_exist', 'NB9BK2888500', 'TCLU7088049', 'NB9BK2888500'),
])
def test_release_status_rule(sub, mbl_no, cntr_no, bkg_no, sample_loader):
    jsontext = sample_loader.read_file(sub, 'sample.json')

    routing_request = ReleaseStatusRoutingRule.build_routing_request(
        container_no=cntr_no, booking_no=bkg_no, base_url=CarrierOneySpider.base_url)
    url = extract_url_from(routing_request=routing_request)

    response = TextResponse(
        url=url,
        body=jsontext,
        encoding='utf-8',
        request=Request(
            url=url,
            meta={
                'container_key': cntr_no
            }
        )
    )

    rule = ReleaseStatusRoutingRule()
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)
