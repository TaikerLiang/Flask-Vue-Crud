from pathlib import Path

import pytest
from scrapy import FormRequest
from scrapy.http import TextResponse

from crawler.core_carrier.rules import RuleManager
from crawler.spiders.carrier_mats import CarrierMatsSpider, TimeRoutingRule
from test.spiders.carrier_mats import container_status


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=container_status, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,mbl_no,meta_status,', [
    ('01_basic', '9271590000', {
        'container_key': 'MATU2332036',
        'timestamp': '1571260260000',
        'description': 'RETURNED FROM CONSIGNEE',
        'location_name': 'LONG BEACH (CA)',
    }),
])
def test_container_status_handler(sub, mbl_no, meta_status, sample_loader):
    html_text = sample_loader.read_file(sub, 'date.html')

    url = 'https://www.matson.com/timezonerange.php/'

    meta_status[RuleManager.META_CARRIER_CORE_RULE_NAME] = TimeRoutingRule.name
    response = TextResponse(
        url=url,
        body=html_text,
        encoding='utf-8',
        request=FormRequest(
            url=url,
            formdata={'date': meta_status['timestamp']},
            meta={
                RuleManager.META_CARRIER_CORE_RULE_NAME: TimeRoutingRule.name,
                'status': meta_status,
            }
        )
    )

    spider = CarrierMatsSpider(mbl_no=mbl_no)
    results = list(spider.parse(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)
