import os

from scrapy.crawler import CrawlerProcess
from scrapy.utils import project

from crawler.spiders.vessel_big_schedules import VesselBigSchedulesSpider

if __name__ == '__main__':
    os.environ[project.ENVVAR] = 'crawler.settings'
    settings = project.get_project_settings()

    process = CrawlerProcess(settings)

    arguments = [
        ('COSU', 'CMA CGM FIDELIO')
    ]

    for scac, vessel_name in arguments:
        kwargs = {
            'scac': scac,
            'vessel_name': vessel_name,
        }
        process.crawl(VesselBigSchedulesSpider, **kwargs)

    process.start()
