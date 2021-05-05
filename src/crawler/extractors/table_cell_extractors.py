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
        td_text_list = cell.css(self.css_query).getall()

        if len(td_text_list) == 1:
            return td_text_list[0].strip()
        elif len(td_text_list) == 0:
            return ''
        else:
            return ' '.join([t.strip() for t in td_text_list])

