from scrapy.crawler import CrawlerProcess

from crawler.spiders.carrier_cosu import CarrierCosuSpider


if __name__ == '__main__':
    process = CrawlerProcess()

    mbl_nos = [
        # 6205506031,
        6210544990, 6213846630, 6085396930, 6199589860,
        # 6201756510, 6201756520, 6202096890, 6204349640, 6204349820,
        # 6205526740, 6205547483, 6210544910, 6210930180, 6210930190,
        # 6212347340, 6212511950, 6213698500, 6213940280, 6214337410,
        # 6214501030, 6215813130, 6215813140, 6215813150, 6215813160,
        # 6215813170, 6215813190, 6216593490, 8021461820, 8021483250,
        # 8021511700, 8021543080,
        # 8021543520,
        # 8021543600,
    ]

    for mbl_no in mbl_nos:
        kwargs = {
            'mbl_no': mbl_no,
        }
        process.crawl(CarrierCosuSpider, **kwargs)

    process.start()
