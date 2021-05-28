import os

from scrapy.crawler import CrawlerProcess
from scrapy.utils import project

from crawler.spiders.terminal_ets import TerminalEtsSpider

if __name__ == '__main__':
    os.environ[project.ENVVAR] = 'crawler.settings'
    settings = project.get_project_settings()

    process = CrawlerProcess(settings)

    container_nos = [
        'EISU8049563',
    ]

    for container_no in container_nos:
        kwargs = {
            'container_no': container_no,
            'save': '1',
        }
        process.crawl(TerminalEtsSpider, **kwargs)

    process.start()
