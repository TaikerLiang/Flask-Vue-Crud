from pathlib import Path

import pytest
import scrapy
from scrapy.http import TextResponse

from crawler.spiders.carrier_hdmu import CarrierHdmuSpider, UrlFactory, ContainerContent
from test.spiders.carrier_hdmu import samples_container

SAMPLE_PATH = Path('./samples_main_info/')


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent / 'samples_container'
    sample_loader.setup(sample_package=samples_container, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,mbl_no,container_content', [
    ('01_first', 'QSWB8011462', ContainerContent(container_no='DFSU6717570', index=2, is_current=False)),
])
def test_parse_container(sample_loader, sub, mbl_no, container_content):

    main_html_file = str(sample_loader.build_file_path(sub, f'container_{container_content.container_no}.html'))
    with open(main_html_file, 'r', encoding="utf-8") as fp:
        httptext = fp.read()

    make_url = UrlFactory()
    url = make_url.build_container_url(mbl_no=mbl_no)

    response = TextResponse(
        url=url,
        encoding='utf-8',
        body=httptext,
        request=scrapy.Request(
            url=url,
            meta={
                'container_content': container_content,
            },
        )
    )

    spider = CarrierHdmuSpider(name=None, mbl_no=mbl_no)
    results = list(spider.parse_container(response))

    # assert
    verify_module = sample_loader.load_sample_module(sub, 'verify_container')
    verifier = verify_module.Verifier(mbl_no=mbl_no)
    verifier.verify(results=results)
