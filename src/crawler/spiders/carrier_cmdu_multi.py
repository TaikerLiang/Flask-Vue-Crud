from crawler.core_carrier.anlc_aplu_cmdu_share_spider import AnlcApluCmduShareSpider


class CarrierCmduSpider(AnlcApluCmduShareSpider):
    name = 'carrier_cmdu_multi'
    base_url = 'http://www.apl.com'
