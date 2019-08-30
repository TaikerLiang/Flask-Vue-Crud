import abc

from scrapy import Selector


class BaseTableCellExtractor:

    @abc.abstractmethod
    def extract(self, cell: Selector):
        pass


class FirstTextTdExtractor(BaseTableCellExtractor):

    def __init__(self, css_query: str = '::text'):
        self.css_query = css_query

    def extract(self, cell: Selector) -> str:
        td_text = cell.css(self.css_query).get()
        return td_text.strip() if td_text else ''
