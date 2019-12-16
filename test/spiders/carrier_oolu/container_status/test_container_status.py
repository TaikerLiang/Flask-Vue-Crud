from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_carrier.rules import RuleManager
from crawler.spiders.carrier_oolu import CarrierOoluSpider, ContainerStatusRule
from test.spiders.carrier_oolu import container_status


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=container_status, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,mbl_no,container_no', [
    ('01_first', '2109051600', 'OOLU910898'),
    ('02_without_lfd_content', '2628633440', 'OOLU907741'),
    ('03_without_lfd_title', '2631411950', 'OOLU121386'),
])
def test_container_status_handler(sub, mbl_no, container_no, sample_loader):
    html_file = sample_loader.read_file(sub, 'sample.html')

    url = (
        'http://moc.oocl.com/party/cargotracking/ct_result_bl.jsf?'
        'ANONYMOUS_TOKEN=kFiFirZYfIHjjEVjGlDTMCCOOCL&ENTRY_TYPE=OOCL'
    )
    response = TextResponse(
        url=url,
        body=html_file,
        encoding='utf-8',
        request=Request(
            url=url,
            meta={
                RuleManager.META_CARRIER_CORE_RULE_NAME: ContainerStatusRule.name,
                'mbl_no': mbl_no,
                'container_no': container_no,
            }
        )
    )

    spider = CarrierOoluSpider(mbl_no=mbl_no)
    results = list(spider.parse(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)
