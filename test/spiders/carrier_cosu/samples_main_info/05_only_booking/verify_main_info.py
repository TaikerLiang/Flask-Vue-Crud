from scrapy import Request

from src.crawler.spiders import carrier_cosu


class Verifier:

    def __init__(self, mbl_no):
        self.mbl_no = mbl_no

    def verify(self, results):
        assert isinstance(results[0], Request)

        url_factory = carrier_cosu.UrlFactory()
        expect_url = url_factory.build_booking_url(self.mbl_no)

        assert results[0].url == expect_url
