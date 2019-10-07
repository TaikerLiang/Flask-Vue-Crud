from scrapy import Request

from src.crawler.spiders import carrier_cosu


class Verifier:

    def __init__(self, mbl_no):
        self.mbl_no = mbl_no

    def verify(self, results):
        assert isinstance(results[0], Request)

        expect_url = f'http://elines.coscoshipping.com/ebtracking/public/booking/{self.mbl_no}'

        assert expect_url in results[0].url
