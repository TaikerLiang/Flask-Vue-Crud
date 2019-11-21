import os

from scrapy.crawler import CrawlerProcess
from scrapy.utils import project

from crawler.spiders.carrier_oocl import CarrierOoclSpider

if __name__ == '__main__':
    os.environ[project.ENVVAR] = 'crawler.settings'
    settings = project.get_project_settings()

    process = CrawlerProcess(settings)

    mbl_nos = [
        # '2626788950',
        # '4104872940',
        # '2625936880',
        # '2625845270',
        # '2626042680',
        # '2626185750',
        '2109051600',
    ]

    for mbl_no in mbl_nos:
        kwargs = {
            'mbl_no': mbl_no,
        }
        process.crawl(CarrierOoclSpider, **kwargs)

    process.start()
