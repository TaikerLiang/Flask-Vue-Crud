import os

from scrapy.crawler import CrawlerProcess
from scrapy.utils import project

from crawler.spiders.carrier_mell import CarrierMellSpider

if __name__ == '__main__':
    os.environ[project.ENVVAR] = 'crawler.settings'
    settings = project.get_project_settings()

    process = CrawlerProcess(settings=settings)

    mbl_nos = [
        'KHH19028854',
        'KHH19028789',
        'KHH19028725',
        'KHH19028681',
        'KHH19028621',
        'KHH19028572',
    ]

    for mbl_no in mbl_nos:
        kwargs = {
            'mbl_no': mbl_no,
        }
        process.crawl(CarrierMellSpider, **kwargs)

    process.start()
