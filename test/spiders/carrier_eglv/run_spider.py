import os

from scrapy.crawler import CrawlerProcess
from scrapy.utils import project

from crawler.spiders.carrier_eglv import CarrierEglvSpider

if __name__ == '__main__':
    os.environ[project.ENVVAR] = 'crawler.settings'
    settings = project.get_project_settings()

    process = CrawlerProcess(settings)

    mbl_nos = [
        '143986250473',
        '003803619868',
        '003901793951',
        '003901365500',
        '143982920890',
        '003901966988',
        '003902245109',
        # '003901796617',     # no such mbl_no
    ]

    for mbl_no in mbl_nos:
        kwargs = {
            'mbl_no': mbl_no,
        }
        process.crawl(CarrierEglvSpider, **kwargs)

    process.start()
