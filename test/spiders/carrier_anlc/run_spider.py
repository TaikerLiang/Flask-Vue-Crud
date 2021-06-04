import os

from scrapy.crawler import CrawlerProcess

from scrapy.utils import project

from crawler.spiders.carrier_anlc_aplu_cmdu import CarrierAnlcSpider

if __name__ == '__main__':
    os.environ[project.ENVVAR] = 'crawler.settings'
    settings = project.get_project_settings()

    process = CrawlerProcess(settings)

    mbl_nos = [
        'AWT0151487',
        'AWT0156149',
        'AWT0154490',
        'AWT0151553',
    ]

    for mbl_no in mbl_nos:
        kwargs = {
            'mbl_no': mbl_no,
            'save': '1',
        }
        process.crawl(CarrierAnlcSpider, **kwargs)

    process.start()
