import abc
from typing import Union

import scrapy
from scrapy import Selector

from crawler.extractors.table_cell_extractors import BaseTableCellExtractor, FirstTextTdExtractor


class HeaderMismatchError(Exception):
    pass


class BaseTable:
    def __init__(self):
        self._td_map = {}       # top_header: {left_header: td, ...}
        self._left_header_set = set()

    @abc.abstractmethod
    def parse(self, table: Selector):
        pass

    def get_cell(self, top: Union[str, int] = 0, left: Union[str, int] = 0) -> Selector:
        try:
            return self._td_map[top][left]
        except KeyError as err:
            raise HeaderMismatchError(repr(err))

    def has_header(self, top=None, left=None) -> bool:
        if top and left:
            return (left in self._left_header_set) and (top in self._td_map)
        elif top is None:
            return left in self._left_header_set
        elif left is None:
            return top in self._td_map
        else:
            return False

    def iter_left_header(self):     # for left header is index
        for i in range(len(self._left_header_set)):
            yield i

    def add_left_header_set(self, left_header: Union[str, int]):
        self._left_header_set.add(left_header)

    def add_td_map(self, td: str, top: Union[str, int], left: Union[str, int]):
        td_dict = self._td_map.setdefault(top, {})
        td_dict[left] = td



class TableExtractor:
    def __init__(self, table_locator: BaseTable):
        self._table_locator = table_locator

    def extract_cell(self, top: Union[str, int] = 0, left: Union[str, int] = 0, extractor: BaseTableCellExtractor = None):
        if not extractor:
            extractor = FirstTextTdExtractor()  # default

        td = self._table_locator.get_cell(top=top, left=left)
        return extractor.extract(cell=td)

    def has_header(self, top=None, left=None) -> bool:
        return self._table_locator.has_header(top=top, left=left)


