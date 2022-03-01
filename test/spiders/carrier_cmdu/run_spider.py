import os

from scrapy.crawler import CrawlerProcess
from scrapy.utils import project

from crawler.spiders.carrier_anlc_aplu_cmdu import CarrierCmduSpider

if __name__ == "__main__":
    os.environ[project.ENVVAR] = "crawler.settings"
    settings = project.get_project_settings()

    process = CrawlerProcess(settings)

    mbl_nos = [
        "AWT0151237",
        "AWT0151814",
        "AWT0151810",
        "AWT0150534",
        "TWN0431755",
        "TWN0429474",
        "CNCC234921",
        "CNPC006475",
        "AWT0153351",
        "CNCC222378",
    ]

    for mbl_no in mbl_nos:
        kwargs = {
            "mbl_no": mbl_no,
            "save": "1",
        }
        process.crawl(CarrierCmduSpider, **kwargs)

    process.start()
