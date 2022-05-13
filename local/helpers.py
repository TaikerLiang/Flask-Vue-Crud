from scrapy_loader import ScrapyLoader


class CrawlerHelper:
    @staticmethod
    def get_crawler(type: str, code: str):
        try:
            return ScrapyLoader(type=type, code=code)
        except KeyError:
            return None
