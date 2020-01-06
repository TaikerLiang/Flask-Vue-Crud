import os

from scrapy.crawler import CrawlerProcess
from scrapy.utils import project

from crawler.spiders.carrier_hdmu import CarrierHdmuSpider

if __name__ == '__main__':
    os.environ[project.ENVVAR] = 'crawler.settings'

    settings = project.get_project_settings()

    process = CrawlerProcess(settings=settings)

    mbl_nos = [
        # 'GJWB1899760',
        # 'QSWB8011462',
        'TYWB0924004',
    ]

    for mbl_no in mbl_nos:
        kwargs = {
            'mbl_no': mbl_no,
        }
        process.crawl(CarrierHdmuSpider, **kwargs)

    process.start()
