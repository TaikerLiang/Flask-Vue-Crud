import os

from scrapy.crawler import CrawlerProcess
from scrapy.utils import project

from crawler.spiders.carrier_sudu_old import CarrierSuduSpider

if __name__ == '__main__':
    os.environ[project.ENVVAR] = 'crawler.settings'
    settings = project.get_project_settings()

    process = CrawlerProcess(settings)

    mbl_nos = [
        # 'SUDUN9NGB075568X',
        # 'SUDUN9NGB061282X',
        'SUDUN9998ALTNBPS',  # mutiple containers
    ]

    for mbl_no in mbl_nos:
        kwargs = {
            'mbl_no': mbl_no,
        }
        process.crawl(CarrierSuduSpider, **kwargs)

    process.start()
