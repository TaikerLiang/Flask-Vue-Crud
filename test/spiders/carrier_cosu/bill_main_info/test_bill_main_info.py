from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.spiders.carrier_cosu import BillMainInfoRoutingRule

from test.spiders.carrier_cosu import bill_main_info


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=bill_main_info, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,mbl_no', [
    ('01_basic', '6199589860'),
    ('02_one_vessel_n_container', '6085396930'),
    ('03_n_vessel_one_container', '8021543080'),
    ('04_n_vessel_m_container', '8021483250'),
    ('05_container_no_is_wrong', '6205749080'),
])
def test_parse_main_info(sample_loader, sub, mbl_no):
    json_text = sample_loader.read_file(sub, 'main_information.json')

    url = f'http://elines.coscoshipping.com/ebtracking/public/bill/{mbl_no}?timestamp=0000000000'

    resp = TextResponse(
        url=url,
        encoding='utf-8',
        body=json_text,
        request=Request(
            url=url,
            meta={
                'mbl_no': mbl_no,
            }
        )
    )

    # action
    rule = BillMainInfoRoutingRule()
    results = list(rule.handle(response=resp))

    # assert
    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)


@pytest.mark.parametrize('sub,mbl_no', [
    ('s01_only_booking', '6216853000'),
    ('s02_invalid_mbl_no_check_booking', '6213846642'),
])
def test_parse_main_info_special(sample_loader, sub, mbl_no):
    json_text = sample_loader.read_file(sub, 'main_information.json')

    url = f'http://elines.coscoshipping.com/ebtracking/public/bill/{mbl_no}?timestamp=0000000000'

    resp = TextResponse(
        url=url,
        encoding='utf-8',
        body=json_text,
        request=Request(url=url, meta={
            'mbl_no': mbl_no,
        })
    )

    # action
    rule = BillMainInfoRoutingRule()
    results = list(rule.handle(response=resp))

    # assert
    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results, mbl_no=mbl_no)
