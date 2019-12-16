from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_carrier.exceptions import CarrierInvalidMblNoError, CarrierResponseFormatError
from crawler.spiders.carrier_hdmu import CarrierHdmuSpider, UrlFactory
from test.spiders.carrier_hdmu import samples_main_info

SAMPLE_PATH = Path('./samples_main_info/')


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent / 'samples_main_info'
    sample_loader.setup(sample_package=samples_main_info, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,mbl_no', [
    ('01_one_container', 'GJWB1899760'),
    ('02_multiple_containers', 'QSWB8011462'),
    ('03_avaliability', 'TAWB0789799'),
    ('04_red_time', 'NXWB1903966'),
    ('05_1_without_lfd', 'QSWB8011632'),
    ('05_2_without_lfd', 'QSWB8011630'),
    ('06_1_original_bl', 'KETC0876470'),
    ('06_2_original_bl', 'QSLB8267628'),
])
def test_parse_main_info(sample_loader, sub, mbl_no):

    main_html_file = str(sample_loader.build_file_path(sub, 'main_information.html'))
    with open(main_html_file, 'r', encoding="utf-8") as fp:
        httptext = fp.read()

    make_url = UrlFactory()
    url = make_url.build_mbl_url()

    response = TextResponse(
        url=url,
        encoding='utf-8',
        body=httptext,
        request=Request(
            url=url,
        )

    )

    spider = CarrierHdmuSpider(name=None, mbl_no=mbl_no)
    results = list(spider.parse_main_info(response))

    # assert
    verify_module = sample_loader.load_sample_module(sub, 'verify_main_info')
    verifier = verify_module.Verifier(mbl_no=mbl_no)
    verifier.verify(results=results)


@pytest.mark.parametrize('sub,mbl_no,expect_exception', [
    ('07_invalid_mbl', 'QSWB801163', CarrierInvalidMblNoError),
    ('08_change_header', 'GJWB1899760', CarrierResponseFormatError),
])
def test_parse_main_info_error(sample_loader, sub, mbl_no, expect_exception):
    main_html_file = str(sample_loader.build_file_path(sub, 'main_information.html'))
    with open(main_html_file, 'r', encoding="utf-8") as fp:
        httptext = fp.read()

    make_url = UrlFactory()
    url = make_url.build_mbl_url()

    response = TextResponse(
        url=url,
        encoding='utf-8',
        body=httptext,
    )

    spider = CarrierHdmuSpider(name=None, mbl_no=mbl_no)
    with pytest.raises(expect_exception):
        list(spider.parse_main_info(response))
