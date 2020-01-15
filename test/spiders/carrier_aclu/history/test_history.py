from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.spiders.carrier_aclu import HistoryRoutingRule
from test.spiders.carrier_aclu import history


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=history, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,mbl_no,', [
    ('01_basic', 'CRSU9164589'),
])
def test_main_info_routing_rule(sub, mbl_no, sample_loader):
    httptext = sample_loader.read_file(sub, 'sample.html')

    url = 'http://www.aclcargo.com/trackCargo.php?EquiPk=34131779522&ShipFk=0&EmoFk=0&acl_track=GCNU4716146&'\
          'Equino=GCNU4716146&verbosity=detail'
    response = TextResponse(
        url=url,
        body=httptext,
        encoding='utf-8',
        request=Request(
            url=url,
        )
    )

    routing_rule = HistoryRoutingRule()
    results = list(routing_rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)
