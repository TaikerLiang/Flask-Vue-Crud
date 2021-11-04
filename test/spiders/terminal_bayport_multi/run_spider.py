import os

from scrapy.crawler import CrawlerProcess
from scrapy.utils import project

from crawler.spiders.terminal_bayport_multi import TerminalBayportMultiSpider

if __name__ == '__main__':
    os.environ[project.ENVVAR] = 'crawler.settings'
    settings = project.get_project_settings()

    process = CrawlerProcess(settings)

    container_nos = 'EITU1744546'

    kwargs = {
        'container_no_list': container_nos,
        'task_id_list': '1',
        'save': '1',
    }
    process.crawl(TerminalBayportMultiSpider, **kwargs)

    process.start()
