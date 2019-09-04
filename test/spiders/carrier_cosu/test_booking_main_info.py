from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from src.crawler.spiders import carrier_cosu

from . import samples_main_info


SAMPLE_PATH = Path('./samples_main_info/')


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent / 'samples_main_info'
    sample_loader.setup(sample_package=samples_main_info, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,mbl_no', [
    ('05_booking', '6216853000'),
])
def test_parse_booking_main_info(sample_loader, sub, mbl_no):
    # load json text
    main_json_file = str(sample_loader.build_file_path(sub, 'main_information.json'))
    with open(main_json_file) as fp:
        json_text = fp.read()

    # mock response
    url_factory = carrier_cosu.UrlFactory()
    url = url_factory.build_booking_url(mbl_no=mbl_no)

    resp = TextResponse(
        url=url,
        encoding='utf-8',
        body=json_text,
        request=Request(url=url, meta={'mbl_no': mbl_no})
    )

    # action
    spider = carrier_cosu.CarrierCosuSpider(name=None, mbl_no=mbl_no)
    results = list(spider.parse_booking_main_info(resp))

    # assert
    verify_module = sample_loader.load_sample_module(sub, 'verify_main_info')
    verifier = verify_module.Verifier(mbl_no=mbl_no)
    verifier.verify(results=results)