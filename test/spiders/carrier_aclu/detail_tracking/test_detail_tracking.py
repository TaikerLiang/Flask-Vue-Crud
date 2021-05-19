from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.spiders.carrier_aclu import DetailTrackingRoutingRule
from test.spiders.carrier_aclu import detail_tracking


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=detail_tracking, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize(
    'sub,container_no,route',
    [
        (
            '01_basic',
            'CRSU9164589',
            '/trackCargo.php?EquiPk=12012928456&ShipFk=0&EmoFk=0&acl_track=CRSU9164589'
            '&Equino=CRSU9164589&verbosity=detail',
        ),
    ],
)
def test_detail_tracking_info_routing_rule(sub, container_no, route, sample_loader):
    httptext = sample_loader.read_file(sub, 'sample.html')
    option = DetailTrackingRoutingRule.build_request_option(route=route, container_no=container_no)

    response = TextResponse(
        url=option.url,
        body=httptext,
        encoding='utf-8',
        request=Request(
            url=option.url,
        ),
    )

    routing_rule = DetailTrackingRoutingRule()
    results = list(routing_rule.handle(response=response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)
