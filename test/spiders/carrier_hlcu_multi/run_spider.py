import os

from scrapy.crawler import CrawlerProcess
from scrapy.utils import project

from crawler.spiders.carrier_hlcu import CarrierHlcuSpider

if __name__ == '__main__':
    os.environ[project.ENVVAR] = 'crawler.settings'
    settings = project.get_project_settings()

    process = CrawlerProcess(settings=settings)

    mbl_nos = [
        # 'HLCUSHA1904CCVX4',
        'HLCUSHA1908JNFF8',
        # 'HLCUSHA1904CFPM3',
    ]

    for mbl_no in mbl_nos:
        kwargs = {
            'mbl_no': mbl_no,
        }
        process.crawl(CarrierHlcuSpider, **kwargs)

    process.start()
