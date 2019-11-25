from pathlib import Path

import pytest

from crawler.core_carrier.exceptions import CarrierInvalidMblNoError
from crawler.spiders.carrier_mscu import CarrierMscuSpider
from test.spiders.carrier_mscu import main_info


class TestDriver:
    def __init__(self, body_text):
        self.body_text = body_text

    def search_mbl_no(self, mbl_no):
        pass

    def get_body_text(self):
        return self.body_text


@pytest.fixture
def sample_loader(sample_loader):
    sample_path = Path(__file__).parent
    sample_loader.setup(sample_package=main_info, sample_path=sample_path)
    return sample_loader


@pytest.mark.parametrize('sub,mbl_no,', [
    ('01_without_ts_port', 'MEDUN4194175'),
    ('02_not_arrival_yet', 'MEDUXA281435'),
    ('03_multi_containers', 'MEDUMY898253'),
    ('04_without_place_of_deliv', 'MEDUH3870076'),
])
def test_main_info_routing_rule(sub, mbl_no, sample_loader):
    http_text = sample_loader.read_file(sub, 'sample.html')

    driver = TestDriver(body_text=http_text)

    spider = CarrierMscuSpider(mbl_no=mbl_no)
    results = list(spider.start_crawl(driver=driver))

    verify_module = sample_loader.load_sample_module(sub, 'verify')
    verify_module.verify(results=results)


@pytest.mark.parametrize('sub,mbl_no,expect_exception', [
    ('e01_invalid_mbl_no', 'MEDUMY898252', CarrierInvalidMblNoError),
])
def test_main_info_handler_mbl_no_error(sub, mbl_no, expect_exception, sample_loader):
    http_text = sample_loader.read_file(sub, 'sample.html')

    driver = TestDriver(body_text=http_text)

    spider = CarrierMscuSpider(mbl_no=mbl_no)
    with pytest.raises(expect_exception):
        list(spider.start_crawl(driver=driver))
