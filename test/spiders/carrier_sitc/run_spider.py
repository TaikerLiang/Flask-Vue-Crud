import os

from scrapy.crawler import CrawlerProcess
from scrapy.utils import project

from crawler.spiders.carrier_sitc import CarrierSitcSpider

if __name__ == '__main__':
    os.environ[project.ENVVAR] = 'crawler.settings'
    settings = project.get_project_settings()

    process = CrawlerProcess(settings)

    params = [
        {'mbl_no': 'SITDNBBK351734', 'container_no': 'TEXU1590997'},
        {'mbl_no': 'SITDNBHP351674', 'container_no': 'TRIU0496357'},
        {'mbl_no': 'SITDNBHP351657', 'container_no': 'TEXU1590148'},
        {'mbl_no': 'SITDKHMO042679', 'container_no': 'TEXU1051634'},
        {'mbl_no': 'SITDKHMO042629', 'container_no': 'TEXU1055964'},
        {'mbl_no': 'SITDNBHP351639', 'container_no': 'SEGU7352846'},
        {'mbl_no': 'SITDNBBK351634', 'container_no': 'TEXU1527910'},
        {'mbl_no': 'SITDNBBK351600', 'container_no': 'TEXU1585331'},
        {'mbl_no': 'SITDKHMO041590', 'container_no': 'SITU0100286'},
        {'mbl_no': 'SITDNBHP351456', 'container_no': 'SEGU7352912'},
        {'mbl_no': 'SITDKHMO041593', 'container_no': 'TRIU0331172'},
        {'mbl_no': 'SITDNBCL351419', 'container_no': 'TEXU1590493'},
    ]

    for param in params:
        kwargs = {
            'mbl_no': param['mbl_no'],
            'container_no': param['container_no'],
        }
        process.crawl(CarrierSitcSpider, **kwargs)

    process.start()
