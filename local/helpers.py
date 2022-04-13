from loaders import CRAWLER_MAP
from scrapy_loader import ScrapyLoader


class CrawlerHelper:
    @staticmethod
    def get_crawler(type: str, code: str, proxy: bool):
        if code in CRAWLER_MAP:
            carrier_class = CRAWLER_MAP[code]
            return carrier_class(proxy=proxy)

        try:
            return ScrapyLoader(type=type, code=code)
        except KeyError:
            return None
