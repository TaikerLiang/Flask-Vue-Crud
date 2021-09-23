from loaders import CRAWLER_MAP


class CrawlerHelper:
    @staticmethod
    def get_crawler(code: str):
        if code in CRAWLER_MAP:
            carrier_class = CRAWLER_MAP[code]
            return carrier_class()
        else:
            return None
