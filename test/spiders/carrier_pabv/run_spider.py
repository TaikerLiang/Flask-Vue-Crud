import os

from scrapy.crawler import CrawlerProcess
from scrapy.utils import project

from crawler.spiders.carrier_pabv import CarrierPabvSpider

if __name__ == '__main__':
    os.environ[project.ENVVAR] = 'crawler.settings'
    settings = project.get_project_settings()

    process = CrawlerProcess(settings)

    mbl_nos = [
        'HPH000040000',
        # 'SHCF90052200',
        # 'NGOC90442600',
        # 'NGNT90707300',
        # 'SHCF90052400',
        # 'NGOC90438300',
        # 'NGNT90701400',
        # 'NKAC90110200',
        # 'SHCF90048400',
        # 'SHCF90047500',
        # 'SHOL90672900',
    ]

    for mbl_no in mbl_nos:
        kwargs = {
            'mbl_no': mbl_no,
        }
        process.crawl(CarrierPabvSpider, **kwargs)

    process.start()
