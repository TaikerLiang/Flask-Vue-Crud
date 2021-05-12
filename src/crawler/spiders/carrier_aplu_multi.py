from crawler.core_carrier.anlc_aplu_cmdu_share_spider import AnlcApluCmduShareSpider


class CarrierApluSpider(AnlcApluCmduShareSpider):
    name = 'carrier_aplu_multi'
    base_url = 'http://www.apl.com'
