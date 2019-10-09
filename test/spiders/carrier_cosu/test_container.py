from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_carrier.rules import RuleManager
from crawler.spiders.carrier_cosu import BillContainerRoutingRule
from src.crawler.spiders import carrier_cosu
from test.spiders.carrier_cosu import samples_container


SAMPLE_PATH = Path('./samples_container/')


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent / 'samples_container'
    sample_loader.setup(sample_package=samples_container, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,mbl_no', [
    ('01_container_no_is_wrong', '6205749080'),
])
def test_container(sample_loader, sub, mbl_no):
    container_json_file = str(sample_loader.build_file_path(sub, 'container.json'))
    with open(container_json_file) as fp:
        json_text = fp.read()

    container_url = f'http://elines.coscoshipping.com/ebtracking/public/bill/containers/{mbl_no}?timestamp=0000000000'

    resp = TextResponse(
        url=container_url,
        encoding='utf-8',
        body=json_text,
        request=Request(url=container_url, meta={
            'mbl_no': mbl_no,
            RuleManager.META_CARRIER_CORE_RULE_NAME: BillContainerRoutingRule.name,
        })
    )

    # action
    spider = carrier_cosu.CarrierCosuSpider(name=None, mbl_no=mbl_no)
    results = list(spider.parse(resp))

    # assert
    verify_module = sample_loader.load_sample_module(sub, 'verify_container')
    verifier = verify_module.Verifier(mbl_no=mbl_no)
    verifier.verify(results=results)
