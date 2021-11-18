from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_carrier.base import SHIPMENT_TYPE_MBL
from crawler.core_carrier.maeu_mccq_safm_multi_share_spider import MainInfoRoutingRule
from crawler.spiders.carrier_mccq_multi import CarrierMccqSpider
from test.spiders.carrier_maeu_mccq_safm_multi.mccq import main_info


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=main_info, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    'sub,mbl_no,',
    [
        ('01_multi_containers_finish', '589898475'),
        ('02_multi_containers_not_finish', '588455529'),
        ('03_data_not_found', '999455999'),
    ],
)
def test_main_info_routing_rule(sub, mbl_no, sample_loader):
    jsontext = sample_loader.read_file(sub, 'sample.json')

    option = MainInfoRoutingRule.build_request_option(search_nos=[mbl_no],
                                                      url_format=CarrierMccqSpider.base_url_format,
                                                      task_ids=['1'],
                                                      )

    response = TextResponse(
        url=option.url,
        body=jsontext,
        encoding='utf-8',
        request=Request(
            url=option.url,
            meta=option.meta,
        ),
    )

    routing_rule = MainInfoRoutingRule(search_type=SHIPMENT_TYPE_MBL)
    results = list(routing_rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)

