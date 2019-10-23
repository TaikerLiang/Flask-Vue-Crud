from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_carrier.rules import RuleManager
from crawler.spiders.carrier_oney_smlm import CarrierSmlmSpider, ContainerStatusRoutingRule
from test.spiders.carrier_oney_smlm.smlm import container_status
from test.spiders.utils import extract_url_from


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=container_status, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,mbl_no,cntr_no,bkg_no,cop_no,base_url', [
    ('01','TATH9C294100', 'SMCU1098525', 'TATH9C294100', 'CTAO9916398264', CarrierSmlmSpider.base_url),
])
def test_container_status_routing_rule(sub, mbl_no, cntr_no, bkg_no, cop_no, base_url, sample_loader):
    jsontext = sample_loader.read_file(sub, 'sample.json')

    routing_request = ContainerStatusRoutingRule.build_routing_request(
        container_no=cntr_no, booking_no=bkg_no, cooperation_no=cop_no, base_url=base_url)
    url = extract_url_from(routing_request=routing_request)

    response = TextResponse(
        url=url,
        body=jsontext,
        encoding='utf-8',
        request=Request(
            url=url,
            meta={
                RuleManager.META_CARRIER_CORE_RULE_NAME: ContainerStatusRoutingRule.name,
                'container_key': cntr_no
            }
        )
    )

    spider = CarrierSmlmSpider(mbl_no=mbl_no)
    results = list(spider.parse(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)
