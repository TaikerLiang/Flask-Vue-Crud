import abc

import scrapy
from scrapy import Selector

from crawler.extractors.table_cell_extractors import BaseTableCellExtractor, FirstTextTdExtractor


class HeaderMismatchError(Exception):
    pass


class BaseTable:
    def __init__(self):
        self._td_map = {}
        self._header_set = set()
        '''
        {
            1 (row1 name):{header1:data1-1, header2:data1-2, ...}
            2 (row2 name):{header1:data2-1, header2:data2-2, ...}
            ...
        }
        '''

    @abc.abstractmethod
    def parse(self, table: Selector):
        pass

    def get_cell(self, header, row) -> Selector:
        try:
            return self._td_map[row][header]
        except KeyError as err:
            raise HeaderMismatchError(repr(err))

    def has_header(self, header=None, row=None) -> bool:
        if header and row:
            return (row in self._td_map.keys()) and (header in self._header_set)
        elif header:
            return (header in self._header_set) and (len(self._td_map) > 0)
        else:
            return row in self._td_map.keys()

    def iter_row(self):
        for i in self._td_map.keys():
            yield i


class TableExtractor:
    def __init__(self, table_locator: BaseTable):
        self._table_locator = table_locator

    def extract_cell(self, header, row=0, extractor: BaseTableCellExtractor = None):
        if not extractor:
            extractor = FirstTextTdExtractor()  # default

        td = self._table_locator.get_cell(header=header, row=row)
        return extractor.extract(cell=td)

    def has_header(self, header=None, row=None) -> bool:
        return self._table_locator.has_header(header=header, row=row)


