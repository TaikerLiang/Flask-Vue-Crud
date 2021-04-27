import os

from scrapy.crawler import CrawlerProcess
from scrapy.utils import project

from crawler.spiders.carrier_cosu import CarrierCosuSpider


if __name__ == '__main__':
    os.environ[project.ENVVAR] = 'crawler.settings'
    settings = project.get_project_settings()

    process = CrawlerProcess(settings=settings)

    mbl_nos = [
        # 6283276882,
        6282200180,
        # 8021543600,
    ]

    for mbl_no in mbl_nos:
        kwargs = {
            'mbl_no': mbl_no,
        }
        process.crawl(CarrierCosuSpider, **kwargs)

    process.start()
