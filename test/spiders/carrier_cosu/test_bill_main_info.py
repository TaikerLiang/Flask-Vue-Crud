from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_carrier.exceptions import CarrierInvalidMblNoError
from crawler.core_carrier.rules import RuleManager
from crawler.spiders.carrier_cosu import BillMainInfoRoutingRule
from src.crawler.spiders import carrier_cosu

from . import samples_main_info


SAMPLE_PATH = Path('./samples_main_info/')


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent / 'samples_main_info'
    sample_loader.setup(sample_package=samples_main_info, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,mbl_no', [
    ('01_basic', '6199589860'),
    ('02_one_vessel_n_container', '6085396930'),
    ('03_n_vessel_one_container', '8021543080'),
    ('04_n_vessel_m_container', '8021483250'),
    ('05_only_booking', '6216853000'),
])
def test_parse_main_info(sample_loader, sub, mbl_no, monkeypatch):
    # monkeypatch.setattr(carrier_cosu, 'build_timestamp', '0000000000')

    # load json text
    main_json_file = str(sample_loader.build_file_path(sub, 'main_information.json'))
    with open(main_json_file) as fp:
        json_text = fp.read()

    url = f'http://elines.coscoshipping.com/ebtracking/public/bill/{mbl_no}?timestamp=0000000000'

    resp = TextResponse(
        url=url,
        encoding='utf-8',
        body=json_text,
        request=Request(url=url, meta={
            'mbl_no': mbl_no,
            RuleManager.META_CARRIER_CORE_RULE_NAME: BillMainInfoRoutingRule.name,
        })
    )

    # action
    spider = carrier_cosu.CarrierCosuSpider(name=None, mbl_no=mbl_no)
    results = list(spider.parse(resp))

    # assert
    verify_module = sample_loader.load_sample_module(sub, 'verify_main_info')
    verifier = verify_module.Verifier(mbl_no=mbl_no)
    verifier.verify(results=results)


@pytest.mark.parametrize('sub,mbl_no,expect_exception', [
    ('06_error', '6213846642', CarrierInvalidMblNoError),
])
def test_parse_main_info_error(sample_loader, sub, mbl_no, expect_exception):
    # load json text
    main_json_file = str(sample_loader.build_file_path(sub, 'main_information.json'))
    with open(main_json_file) as fp:
        json_text = fp.read()

    url = f'http://elines.coscoshipping.com/ebtracking/public/bill/{mbl_no}?timestamp=0000000000'

    resp = TextResponse(
        url=url,
        encoding='utf-8',
        body=json_text,
        request=Request(url=url, meta={
            'mbl_no': mbl_no,
            RuleManager.META_CARRIER_CORE_RULE_NAME: BillMainInfoRoutingRule.name,
        })
    )

    # action
    spider = carrier_cosu.CarrierCosuSpider(name=None, mbl_no=mbl_no)

    with pytest.raises(expect_exception):
        spider.parse(resp)
