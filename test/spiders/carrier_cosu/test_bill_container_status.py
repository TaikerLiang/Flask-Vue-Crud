from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_carrier.rules import RuleManager
from crawler.spiders.carrier_cosu import BillContainerStatusRoutingRule
from src.crawler.spiders import carrier_cosu

from . import samples_container_status

SAMPLE_PATH = Path('./samples_container_status/')
pytest.register_assert_rewrite(samples_container_status.__name__)


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent / 'samples_container_status'
    sample_loader.setup(sample_package=samples_container_status, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,mbl_no,container', [
    ('01_one_vessel', '6199589860', 'CSNU6276212'),
    ('02_two_vessel', '8021543080', 'FCIU5635365'),
    ('03_three_vessel', '8021543520', 'TRHU2558351'),
    ('03_01_three_vessel_no_third_vessel', '8021543600', 'CCLU7463821'),
])
def test_parse_container(sample_loader, sub, mbl_no, container):
    container_no = container

    # load json text
    main_json_file = str(sample_loader.build_file_path(sub, f'status_{container_no}.json'))

    with open(main_json_file) as fp:
        json_text = fp.read()

    # mock response
    url = f'http://elines.coscoshipping.com/ebtracking/public/container/status/{container_no}' \
          f'?billNumber={mbl_no}&timestamp=0000000000'

    resp = TextResponse(
        url=url,
        encoding='utf-8',
        body=json_text,
        request=Request(url=url, meta={
            'mbl_no': mbl_no,
            RuleManager.META_CARRIER_CORE_RULE_NAME: BillContainerStatusRoutingRule.name,
        })
    )

    # action
    spider = carrier_cosu.CarrierCosuSpider(name=None, mbl_no=mbl_no)
    results = list(spider.parse(resp))

    # assert
    verify_module = sample_loader.load_sample_module(sub, 'verify_container_status')
    verifier = verify_module.Verifier(mbl_no=mbl_no)
    verifier.verify(results=results)
