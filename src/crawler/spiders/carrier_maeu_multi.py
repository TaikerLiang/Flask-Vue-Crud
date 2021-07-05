from crawler.core_carrier.maeu_mccq_safm_multi_share_spider import MaeuMccqSafmShareSpider

class CarrierMaeuSpider(MaeuMccqSafmShareSpider):
    name = 'carrier_maeu_multi'
    base_url_format = 'https://api.maerskline.com/track/{search_no}'