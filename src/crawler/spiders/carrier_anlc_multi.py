from crawler.core_carrier.anlc_aplu_cmdu_share_spider import AnlcApluCmduShareSpider


class CarrierAnlcSpider(AnlcApluCmduShareSpider):
    name = 'carrier_anlc_multi'
    base_url = 'https://www.anl.com.au'
