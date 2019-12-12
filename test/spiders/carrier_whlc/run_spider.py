import os

from scrapy.crawler import CrawlerProcess
from scrapy.utils import project

from crawler.spiders.carrier_whlc import CarrierWhlcSpider

if __name__ == '__main__':
    os.environ[project.ENVVAR] = 'crawler.settings'
    settings = project.get_project_settings()

    process = CrawlerProcess(settings)

    mbl_nos = [
        '0249538702',
        '0349531933',
        '0269534364',
        '0249541639',
        '0259A36452',
        '0249538701',
        '0249538700',
        '0259612621',
    ]

    for mbl_no in mbl_nos:
        kwargs = {
            'mbl_no': mbl_no,
        }
        process.crawl(CarrierWhlcSpider, **kwargs)

    process.start()