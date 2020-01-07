import os

from scrapy.crawler import CrawlerProcess
from scrapy.utils import project

from crawler.spiders.carrier_gosu_ssph import CarrierSsphSpider

if __name__ == '__main__':
    os.environ[project.ENVVAR] = 'crawler.settings'
    settings = project.get_project_settings()

    process = CrawlerProcess(settings)

    mbl_nos = [
        'SSPHJOR8017471',
        'SSPHLAX0140904',
        'SSPHLAX0140932',
        'SSPHLAX0137883',
        'SSPHLAX0137876',
        'SSPHLAX0137876',
    ]

    for mbl_no in mbl_nos:
        kwargs = {
            'mbl_no': mbl_no,
        }
        process.crawl(CarrierSsphSpider, **kwargs)

    process.start()
