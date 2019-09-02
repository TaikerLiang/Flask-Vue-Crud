from pathlib import Path

import pytest
from scrapy import Request
from scrapy.http import TextResponse

from crawler.core_carrier.exceptions import CarrierInvalidMblNoError
from crawler.spiders.carrier_aplu_cmdu import RoutingManager, CarrierCmduSpider, SharedUrlFactory, UrlSpec
from . import samples_main_info


SAMPLE_PATH = Path('./samples_main_info/')


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent / 'samples_main_info'
    sample_loader.setup(sample_package=samples_main_info, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,mbl_no', [
    ('01_not_finish', 'CNPC001499'),
    ('02_finish', 'NBSF300899'),
    ('03_multiple_containers', 'NBSF301194'),
    ('04_por', 'GGZ1004320'),
    ('05_dest', 'NBSF301068'),
])
def test_parse(sample_loader, sub, mbl_no):
    html_file = str(sample_loader.build_file_path(sub, 'main_information.html'))
    with open(html_file) as fp:
        html_text = fp.read()

    url_factory = SharedUrlFactory(home_url=CarrierCmduSpider.home_url, mbl_no=mbl_no)
    url_builder = url_factory.get_bill_url_builder()
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

    spider = CarrierCmduSpider(name=None, mbl_no=mbl_no)
    results = list(spider.parse(response))

    verify_module = sample_loader.load_sample_module(sub, 'verify_main_info')
    verifier = verify_module.Verifier(mbl_no=mbl_no)
    verifier.verify(results=results)


@pytest.mark.parametrize('sub,mbl_no,expect_exception', [
    ('06_invalid_mbl_no', 'NBSF300898', CarrierInvalidMblNoError),
])
def test_parse_error(sample_loader, sub, mbl_no, expect_exception):
    html_file = str(sample_loader.build_file_path(sub, 'main_information.html'))
    with open(html_file) as fp:
        html_text = fp.read()

    url_factory = SharedUrlFactory(home_url=CarrierCmduSpider.home_url, mbl_no=mbl_no)
    url_builder = url_factory.get_bill_url_builder()
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

    spider = CarrierCmduSpider(name=None, mbl_no=mbl_no)

    with pytest.raises(expect_exception):
        spider.parse(response)
