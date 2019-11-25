from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_carrier.rules import RuleManager
from crawler.spiders.carrier_eglv import CarrierEglvSpider, ContainerStatusRoutingRule
from test.spiders.carrier_eglv import container_status


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=container_status, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,mbl_no,container_no', [
    ('01_single_table', '003902245109', 'HMCU9173542'),
    ('02_two_table', '003902385989', 'EITU1673822'),

])
def test_container_status_handler(sub, mbl_no, container_no, sample_loader):
    html_file = str(sample_loader.build_file_path(sub, 'sample.html'))
    with open(html_file, 'r', encoding='utf-8') as fp:
        html_text = fp.read()

    response = TextResponse(
        url='https://www.shipmentlink.com/servlet/TDB1_CargoTracking.do',
        body=html_text,
        encoding='utf-8',
        request=Request(
            url='https://www.shipmentlink.com/servlet/TDB1_CargoTracking.do',
            meta={
                RuleManager.META_CARRIER_CORE_RULE_NAME: ContainerStatusRoutingRule.name,
                'container_no': container_no,
            }
        )
    )

    spider = CarrierEglvSpider(mbl_no=mbl_no)
    results = list(spider.parse(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verifier = verify_module.Verifier()
    verifier.verify(results=results)