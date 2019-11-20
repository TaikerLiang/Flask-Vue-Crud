from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.spiders.carrier_aplu_cmdu_anlc import UrlSpec, CarrierApluSpider, RoutingManager, SharedUrlFactory
from test.spiders.carrier_aplu_cmdu_anlc.aplu import container


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=container, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,mbl_no', [
    ('01_basic', 'SHSE015942'),
    ('02_no_pod_time_and_status', 'AYU0320031'),
])
def test_parse(sample_loader, sub, mbl_no):
    html_text = sample_loader.read_file(sub, 'container.html')

    url_factory = SharedUrlFactory(home_url=CarrierApluSpider.home_url, mbl_no=mbl_no)
    url_builder = url_factory.get_container_url_builder()
    url = url_builder.build_url_from_spec(spec=UrlSpec())

    response = TextResponse(
        url=url,
        encoding='utf-8',
        body=html_text,
        request=Request(
            url=url,
            meta={RoutingManager.META_ROUTING_RULE: 'HANDLE_CONTAINER'},
        ),
    )

    spider = CarrierApluSpider(name=None, mbl_no=mbl_no)
    results = list(spider.parse(response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)
