from crawler.core_carrier.oney_smlm_multi_share_spider import OneySmlmSharedSpider


class CarrierSmlmSpider(OneySmlmSharedSpider):
    name = 'carrier_smlm_multi'
    base_url = 'https://esvc.smlines.com/smline/CUP_HOM_3301GS.do'
