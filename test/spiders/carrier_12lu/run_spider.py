import os

from scrapy.crawler import CrawlerProcess
from scrapy.utils import project

from crawler.spiders.carrier_12lu import Carrier12luSpider

if __name__ == '__main__':
    os.environ[project.ENVVAR] = 'crawler.settings'
    settings = project.get_project_settings()

    process = CrawlerProcess(settings=settings)

    mbl_nos = [
        'NOSNB9GX16042',
        'NOSNB9YK51244',
        'NOSNB9GX15877',
        'NOSNB9TZ35829',
        'NOSNB9GX15802',
        'NOSNB9GX15773',
    ]

    for mbl_no in mbl_nos:
        kwargs = {
            'mbl_no': mbl_no,
        }
        process.crawl(Carrier12luSpider, **kwargs)

    process.start()
