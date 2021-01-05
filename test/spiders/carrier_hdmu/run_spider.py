import os

from scrapy.crawler import CrawlerProcess
from scrapy.utils import project

from crawler.spiders.carrier_hdmu import CarrierHdmuSpider

if __name__ == '__main__':
    os.environ[project.ENVVAR] = 'crawler.settings'

    settings = project.get_project_settings()

    process = CrawlerProcess(settings=settings)

    mbl_nos = [
        # 'QSWB8014265',
        # 'QSWB9354269',
        # 'KAWB1113397',
        # 'TACA1094192',
        # 'MLWB0150473',
        # 'YNWB2432642',
        # 'TYWB1105254',
        # 'KEWB1117764',
        # 'GJWB2466893',
        # 'NXWB0351471',
        # 'MPWB3821952',
        # 'TACA1099870',
        'HDMUBKKM02611700',
        'HDMUCANM47289400',
        'HDMUSHAZ14206200',
        'HDMUCANM46690900',
        'HDMUCANM37487100',
        'HDMUCANM33421600',
        'HDMUCANM80199600',
        'HDMUCANM82064900',
    ]

    for mbl_no in mbl_nos:
        kwargs = {
            'mbl_no': mbl_no,
            'save': '1',
        }
        process.crawl(CarrierHdmuSpider, **kwargs)

    process.start()
