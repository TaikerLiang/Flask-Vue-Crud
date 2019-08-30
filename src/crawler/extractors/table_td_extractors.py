import abc

from scrapy import Selector


class BaseTdExtractor:

    @abc.abstractmethod
    def extract(self, td: Selector):
        pass


class FirstTextTdExtractor(BaseTdExtractor):

    def __init__(self, css_query: str = '::text'):
        self.css_query = css_query

    def extract(self, td: Selector) -> str:
        td_text = td.css(self.css_query).get()
        return td_text.strip() if td_text else ''
