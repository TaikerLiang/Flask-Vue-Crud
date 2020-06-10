import os

from scrapy.crawler import CrawlerProcess
from scrapy.utils import project

from crawler.spiders.terminal_fenix import TerminalFenixSpider

if __name__ == '__main__':
    os.environ[project.ENVVAR] = 'crawler.settings'
    settings = project.get_project_settings()

    process = CrawlerProcess(settings)

    params = [
        {'mbl_no': '4049820105', 'container_no': '1'},
        {'mbl_no': '2638621180', 'container_no': '2'},
        {'mbl_no': '2639041240', 'container_no': '3'},
        {'mbl_no': '2638924620', 'container_no': '4'},
        {'mbl_no': '6262168440', 'container_no': '5'},
        {'mbl_no': '146000246454', 'container_no': '6'},
        {'mbl_no': '2638732540', 'container_no': '7'},
        {'mbl_no': '2638922340', 'container_no': '8'},
        {'mbl_no': '149001269738', 'container_no': '9'},
        {'mbl_no': '2637612890', 'container_no': '10'},
        # {'mbl_no': 'SITDKHMO041593', 'container_no': 'TRIU0331172'},
        # {'mbl_no': 'SITDNBCL351419', 'container_no': 'TEXU1590493'},
    ]

    for param in params:
        kwargs = {
            'container_no': param['container_no'],
            'mbl_no': param['mbl_no'],
            'save': '1',
        }
        process.crawl(TerminalFenixSpider, **kwargs)

    process.start()
