import os

from scrapy.crawler import CrawlerProcess
from scrapy.utils import project

from crawler.spiders.carrier_ymlu import CarrierYmluSpider

if __name__ == '__main__':
    os.environ[project.ENVVAR] = 'crawler.settings'
    settings = project.get_project_settings()

    process = CrawlerProcess(settings)

    mbl_nos = [
        'I209384150',
    ]

    for mbl_no in mbl_nos:
        kwargs = {
            'mbl_no': mbl_no,
        }
        process.crawl(CarrierYmluSpider, **kwargs)

    process.start()
