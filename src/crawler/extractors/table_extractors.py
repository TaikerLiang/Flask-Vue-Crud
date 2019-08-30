import abc

from scrapy import Selector

from crawler.extractors.table_cell_extractors import BaseTableCellExtractor, FirstTextTdExtractor


class HeaderMismatchError(Exception):
    pass


class BaseTableLocator:

    @abc.abstractmethod
    def parse(self, table: Selector):
        pass

    @abc.abstractmethod
    def get_cell(self, top, left) -> Selector:
        pass

    @abc.abstractmethod
    def has_header(self, top=None, left=None) -> bool:
        pass


class TableInfo:

    def __init__(self, table_locator: BaseTableLocator):
        self._table_locator = table_locator

    def extract_cell(self, top, left, extractor: BaseTableCellExtractor = None):
        if not extractor:
            extractor = FirstTextTdExtractor()  # default

        td = self._table_locator.get_cell(top=top, left=left)
        return extractor.extract(cell=td)

    def has_header(self, top=None, left=None) -> bool:
        return self._table_locator.has_header(top=top, left=left)


class TableExtractor:

    @staticmethod
    def extract(table: Selector, locator: BaseTableLocator) -> TableInfo:
        locator.parse(table=table)
        return TableInfo(table_locator=locator)


class TopHeaderTableLocator(BaseTableLocator):

    def __init__(self):
        self._td_map = {}  # top_header: [td, ...]

    def parse(self, table: Selector):
        top_header_list = []

        for th in table.css('thead th'):
            top_header = th.css('::text').get().strip()
            top_header_list.append(top_header)
            self._td_map[top_header] = []

        for tr in table.css('tbody tr'):
            for top_index, td in enumerate(tr.css('td')):
                top = top_header_list[top_index]
                self._td_map[top].append(td)

    def get_cell(self, top, left) -> Selector:
        try:
            return self._td_map[top][left]
        except (KeyError, IndexError) as err:
            raise HeaderMismatchError(repr(err))

    def has_header(self, top=None, left=None) -> bool:
        return (top in self._td_map) and (left is None)


class TopLeftHeaderTableLocator(BaseTableLocator):

    def __init__(self):
        self._td_map = {}  # top_header: {left_header: td, ...}
        self._left_header_set = set()

    def parse(self, table: Selector):
        top_header_map = {}  # top_index: top_header

        for index, th in enumerate(table.css('thead th')):
            if index == 0:
                continue  # ignore top-left header

            top_header = th.css('::text').get().strip()
            top_header_map[index] = top_header
            self._td_map[top_header] = {}

        for tr in table.css('tbody tr'):
            td_list = list(tr.css('td'))

            left_header = td_list[0].css('::text').get().strip()
            self._left_header_set.add(left_header)

            for top_index, td in enumerate(td_list[1:], start=1):
                top = top_header_map[top_index]
                self._td_map[top][left_header] = td

    def get_cell(self, top, left) -> Selector:
        try:
            return self._td_map[top][left]
        except KeyError as err:
            raise HeaderMismatchError(repr(err))

    def has_header(self, top=None, left=None) -> bool:
        if top is None:
            return left in self._left_header_set
        elif left is None:
            return top in self._td_map
        else:
            return False


class LeftHeaderTableLocator(BaseTableLocator):

    def __init__(self):
        self._td_map = {}  # top_index: {left_header: td, ...}
        self._left_header_set = set()

    def parse(self, table: Selector):
        top_index_set = set()

        for tr in table.css('tbody tr'):
            left_header = tr.css('th ::text').get().strip()
            self._left_header_set.add(left_header)

            for top_index, td in enumerate(tr.css('td')):
                top_index_set.add(top_index)
                td_dict = self._td_map.setdefault(top_index, {})
                td_dict[left_header] = td

    def get_cell(self, top, left) -> Selector:
        try:
            return self._td_map[top][left]
        except KeyError as err:
            raise HeaderMismatchError(repr(err))

    def has_header(self, top=None, left=None) -> bool:
        return (top is None) and (left in self._left_header_set)
