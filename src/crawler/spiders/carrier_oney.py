from crawler.core_carrier.oney_smlm_share_spider import OneySmlmSharedSpider


class CarrierOneySpider(OneySmlmSharedSpider):
    name = 'carrier_oney'
    base_url = 'https://ecomm.one-line.com/ecom/CUP_HOM_3301GS.do'