from crawler.core_carrier.maeu_mccq_safm_share_spider import MaeuMccqSafmShareSpider

class CarrierMccqSpider(MaeuMccqSafmShareSpider):
    name = 'carrier_mccq'
    base_url_format = 'https://api.maerskline.com/track/{search_no}?operator=mcpu'