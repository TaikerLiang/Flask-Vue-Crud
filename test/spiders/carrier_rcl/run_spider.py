import os

from scrapy.crawler import CrawlerProcess
from scrapy.utils import project

from crawler.spiders.carrier_rcl import CarrierRclSpider

if __name__ == '__main__':
    os.environ[project.ENVVAR] = 'crawler.settings'
    settings = project.get_project_settings()

    process = CrawlerProcess(settings)

    mbl_nos = [
        'NGBCB19030160',
        'NGBCB19030998',
        'NGBCB19031315',
        'NGBCB19030020',
        'NGBCB19029942',
        'NGBCB19029593',
    ]

    for mbl_no in mbl_nos:
        kwargs = {
            'mbl_no': mbl_no,
        }
        process.crawl(CarrierRclSpider, **kwargs)

    process.start()
