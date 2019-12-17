import os

from scrapy.crawler import CrawlerProcess

from scrapy.utils import project

from crawler.spiders.carrier_aplu_cmdu_anlc import CarrierAnlcSpider

if __name__ == '__main__':
    os.environ[project.ENVVAR] = 'crawler.settings'
    settings = project.get_project_settings()

    process = CrawlerProcess(settings)

    mbl_nos = [
        'AWT0143454',
        # 'AWT0143370',
        # 'AWT0143320',
        # 'AWT0143329',
    ]

    for mbl_no in mbl_nos:
        kwargs = {
            'mbl_no': mbl_no,
        }
        process.crawl(CarrierAnlcSpider, **kwargs)

    process.start()
