import os

from scrapy.crawler import CrawlerProcess

from scrapy.utils import project

from crawler.spiders.carrier_aplu_cmdu import CarrierApluSpider

if __name__ == '__main__':
    os.environ[project.ENVVAR] = 'crawler.settings'
    settings = project.get_project_settings()

    process = CrawlerProcess(settings)

    mbl_nos = [
        'AXK0185154',
        # 'AXK0185155',
        # 'XHMN810789',
        # 'AWB0135426',
    ]

    for mbl_no in mbl_nos:
        kwargs = {
            'mbl_no': mbl_no,
        }
        process.crawl(CarrierApluSpider(mbl_no=mbl_no), **kwargs)

    process.start()
