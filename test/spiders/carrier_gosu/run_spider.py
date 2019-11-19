import os

from scrapy.crawler import CrawlerProcess
from scrapy.utils import project

from crawler.spiders.carrier_gosu import CarrierGosuSpider

if __name__ == '__main__':
    os.environ[project.ENVVAR] = 'crawler.settings'
    settings = project.get_project_settings()

    process = CrawlerProcess(settings)

    mbl_nos = [
        'GOSUNGB9490903',
        'GOSUNGB9490855',
        'GOSUNGB9490849',
        'GOSUNGB9490840',
        'GOSUNGB9490813',
        'GOSUNGB9490815',
    ]

    for mbl_no in mbl_nos:
        kwargs = {
            'mbl_no': mbl_no,
        }
        process.crawl(CarrierGosuSpider, **kwargs)

    process.start()
