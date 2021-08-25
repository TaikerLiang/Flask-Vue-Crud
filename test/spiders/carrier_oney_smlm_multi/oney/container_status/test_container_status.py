from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.spiders.carrier_oney_multi import CarrierOneySpider
from crawler.core_carrier.oney_smlm_multi_share_spider import ContainerStatusRoutingRule
from test.spiders.carrier_oney_smlm_multi.oney import container_status


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=container_status, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    'sub,mbl_no,cntr_no,bkg_no,cop_no',
    [
        ('01', 'SH9FSK690300', 'CLHU9129958', 'SH9FSK690300', 'CSHA9925486010'),
        ('02_event_with_empty_time', 'SGNVG4590800', 'FDCU0637220', 'SGNVG4590800', 'CSGN9A24583850'),
    ],
)
def test_container_status_handle(sub, mbl_no, cntr_no, bkg_no, cop_no, sample_loader):
    jsontext = sample_loader.read_file(sub, 'sample.json')

    option = ContainerStatusRoutingRule.build_request_option(
        container_no=cntr_no, booking_no=bkg_no, cooperation_no=cop_no, base_url=CarrierOneySpider.base_url, task_id=1,
    )

    response = TextResponse(
        url=option.url,
        body=jsontext,
        encoding='utf-8',
        request=Request(
            url=option.url,
            meta=option.meta,
        ),
    )

    rule = ContainerStatusRoutingRule()
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)
