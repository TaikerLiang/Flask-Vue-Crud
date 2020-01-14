from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.spiders.carrier_cosu import BillContainerStatusRoutingRule

from test.spiders.carrier_cosu import bill_container_status


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=bill_container_status, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,mbl_no,container_no', [
    ('01_one_vessel', '6199589860', 'CSNU6276212'),
    ('02_two_vessel', '8021543080', 'FCIU5635365'),
    ('03_three_vessel', '8021543520', 'TRHU2558351'),
    ('04_three_vessel_no_third_vessel', '8021543600', 'CCLU7463821'),
])
def test_parse_container(sample_loader, sub, mbl_no, container_no):
    json_text = sample_loader.read_file(sub, 'status.json')

    # mock response
    url = (
        f'http://elines.coscoshipping.com/ebtracking/public/container/status/{container_no}'
        f'?billNumber={mbl_no}&timestamp=0000000000'
    )

    container_key = container_no[:10]

    resp = TextResponse(
        url=url,
        encoding='utf-8',
        body=json_text,
        request=Request(
            url=url,
            meta={
                'mbl_no': mbl_no,
                'container_key': container_key,
            },
        )
    )

    # action
    rule = BillContainerStatusRoutingRule()
    results = list(rule.handle(response=resp))

    # assert
    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)
