import os

from scrapy.crawler import CrawlerProcess

from scrapy.utils import project

from crawler.spiders.carrier_aplu_cmdu import CarrierCmduSpider

if __name__ == '__main__':
    os.environ[project.ENVVAR] = 'crawler.settings'
    settings = project.get_project_settings()

    process = CrawlerProcess(settings)

    mbl_nos = [
        'NBSF301194',
    ]

    for mbl_no in mbl_nos:
        kwargs = {
            'mbl_no': mbl_no,
        }
        process.crawl(CarrierCmduSpider, **kwargs)

    process.start()
