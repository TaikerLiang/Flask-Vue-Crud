from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.spiders.carrier_cosu import BillContainerRoutingRule
from test.spiders.carrier_cosu import bill_container


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=bill_container, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,mbl_no', [
    ('01_container_no_is_wrong', '6205749080'),
    ('02_mismatch_container_index_and_uuid', '6217207070'),
])
def test_container(sample_loader, sub, mbl_no):
    json_text = sample_loader.read_file(sub, 'container.json')

    container_url = (
        f'http://elines.coscoshipping.com/ebtracking/public/bill/containers/{mbl_no}?timestamp=0000000000'
    )

    resp = TextResponse(
        url=container_url,
        encoding='utf-8',
        body=json_text,
        request=Request(url=container_url, meta={
            'mbl_no': mbl_no,
        })
    )

    # action
    rule = BillContainerRoutingRule()
    results = list(rule.handle(response=resp))

    # assert
    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results, mbl_no=mbl_no)
