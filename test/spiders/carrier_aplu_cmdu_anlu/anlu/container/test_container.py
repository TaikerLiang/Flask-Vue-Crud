from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.spiders.carrier_aplu_cmdu_anlu import SharedUrlFactory, UrlSpec, RoutingManager, CarrierAnluSpider
from test.spiders.carrier_aplu_cmdu_anlu.anlu import container


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=container, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,mbl_no', [
    ('01_basic', 'BHCU2231403'),
    ('02_pod_status_is_remaining', 'TEXU1028151'),
])
def test_parse(sample_loader, sub, mbl_no):
    html_text = sample_loader.read_file(sub, 'container.html')

    url_factory = SharedUrlFactory(home_url=CarrierAnluSpider.home_url, mbl_no=mbl_no)
    url_builder = url_factory.get_container_url_builder()
    url = url_builder.build_url_from_spec(spec=UrlSpec())

    response = TextResponse(
        url=url,
        encoding='utf-8',
        body=html_text,
        request=Request(
            url=url,
            meta={RoutingManager.META_ROUTING_RULE: 'HANDLE_FIRST_TIER'}
        )
    )

    spider = CarrierAnluSpider(name=None, mbl_no=mbl_no)
    results = list(spider.parse(response))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)
