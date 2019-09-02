from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.spiders.carrier_aplu_cmdu import UrlSpec, RoutingManager, CarrierCmduSpider, SharedUrlFactory
from . import samples_container


SAMPLE_PATH = Path('./samples_container/')


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent / 'samples_container'
    sample_loader.setup(sample_package=samples_container, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,mbl_no,container_no', [
    ('01_basic', 'NBSF301194', 'ECMU9893257'),
])
def test_parse(sample_loader, sub, mbl_no, container_no):
    html_file = str(sample_loader.build_file_path(sub, f'{container_no}.html'))
    with open(html_file) as fp:
        html_text = fp.read()

    url_factory = SharedUrlFactory(home_url=CarrierCmduSpider.home_url, mbl_no=mbl_no)
    url_builder = url_factory.get_container_url_builder()
    url_spec = UrlSpec(container_no=container_no)
    url = url_builder.build_url_from_spec(spec=url_spec)

    response = TextResponse(
        url=url,
        encoding='utf-8',
        body=html_text,
        request=Request(
            url=url,
            meta={RoutingManager.META_ROUTING_RULE: 'HANDLE_CONTAINER'},
        ),
    )

    spider = CarrierCmduSpider(name=None, mbl_no=mbl_no)
    results = list(spider.parse(response))

    verify_module = sample_loader.load_sample_module(sub, 'verify_container')
    verifier = verify_module.Verifier(mbl_no=mbl_no)
    verifier.verify(results=results)
