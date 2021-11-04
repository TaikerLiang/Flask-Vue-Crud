from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.spiders.carrier_oney_multi import CarrierOneySpider
from crawler.core_carrier.oney_smlm_multi_share_spider import RailInfoRoutingRule
from test.spiders.carrier_oney_smlm_multi.oney import rail_info


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=rail_info, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    'sub,mbl_no,cntr_no,cop_no',
    [
        ('01', 'SZPVD5837613', 'BEAU5297455', 'CSZP9819161088'),
    ],
)
def test_rail_information_handle(sub, mbl_no, cntr_no, cop_no, sample_loader):
    jsontext = sample_loader.read_file(sub, 'sample.json')

    option = RailInfoRoutingRule.build_request_option(
        container_no=cntr_no, cooperation=cop_no, base_url=CarrierOneySpider.base_url, task_id=1,
    )

    response = TextResponse(
        url=option.url,
        body=jsontext,
        encoding='utf-8',
        request=Request(url=option.url, meta={'container_key': cntr_no, 'task_id': 1, }),
    )

    rule = RailInfoRoutingRule()
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)
