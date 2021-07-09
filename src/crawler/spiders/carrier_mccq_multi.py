from crawler.core_carrier.maeu_mccq_safm_multi_share_spider import MaeuMccqSafmShareSpider

class CarrierMccqSpider(MaeuMccqSafmShareSpider):
    name = 'carrier_mccq_multi'
    base_url_format = 'https://api.maerskline.com/track/{search_no}?operator=mcpu'