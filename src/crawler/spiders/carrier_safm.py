from crawler.core_carrier.maeu_mccq_safm_share_spider import MaeuMccqSafmShareSpider

class CarrierSafmSpider(MaeuMccqSafmShareSpider):
    name = 'carrier_safm'
    base_url_format = 'https://api.maerskline.com/track/{search_no}?operator=safm'