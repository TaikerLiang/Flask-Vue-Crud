import os

from scrapy.crawler import CrawlerProcess
from scrapy.utils import project

from crawler.spiders.carrier_sitc import CarrierSitcSpider

if __name__ == '__main__':
    os.environ[project.ENVVAR] = 'crawler.settings'
    settings = project.get_project_settings()

    process = CrawlerProcess(settings)

    params = [
        {'mbl_no': 'SITDNBBK351734', 'container_no': 'TEXU1590997'}
    ]

    for param in params:
        kwargs = {
            'mbl_no': param['mbl_no'],
            'container_no': param['container_no'],
        }
        process.crawl(CarrierSitcSpider, **kwargs)

    process.start()
