from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_carrier.rules import RuleManager
from crawler.spiders.carrier_pabv import ContainerRoutingRule
from test.spiders.carrier_pabv import container


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=container, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    'sub,mbl_no,container_id',
    [
        ('01_normal', 'NKAI90055900', 'PCIU9477648'),
        ('02_ignore_pending_events', 'NGRI90598700', 'PCIU0142052'),
    ],
)
def test_container_handler(sub, mbl_no, container_id, sample_loader):
    json_text = sample_loader.read_file(sub, 'sample.json')

    url = (
        'https://www.pilship.com/shared/ajax/'
        f'?fn=get_track_container_status&search_type=bl&search_type_no={mbl_no}&ref_num={container_id}'
    )

    response = TextResponse(
        url=url,
        body=json_text,
        encoding='utf-8',
        request=Request(
            url=url,
            meta={
                RuleManager.META_CARRIER_CORE_RULE_NAME: ContainerRoutingRule.name,
                'mbl_no': mbl_no,
                'cookies': '',
                'container_id': container_id,
            },
        ),
    )

    rule = ContainerRoutingRule()
    results = list(rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verifier = verify_module.Verifier()
    verifier.verify(results=results)
