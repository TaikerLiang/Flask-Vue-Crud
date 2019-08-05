from scrapy import Request

from crawler.core_mbl.items import MblItem, VesselItem, LocationItem
from crawler.spiders import carrier_cosu


class Verifier:

    def __init__(self, mbl_no):
        self.mbl_no = mbl_no

    def verify(self, results):
        assert len(results) == 1
        assert results[0] == 'Wrong Mbl_no'
