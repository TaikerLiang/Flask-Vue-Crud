from typing import Set, Dict

from scrapy import Selector


class HeaderMismatchError(Exception):
    pass


class BaseTdExtractor:

    def extract(self, td: Selector):
        raise NotImplementedError


class FirstTextTdExtractor(BaseTdExtractor):

    def __init__(self, css_query: str = '::text'):
        self.css_query = css_query

    def extract(self, td: Selector) -> str:
        td_text = td.css(self.css_query).get()
        return td_text.strip() if td_text else ''


class TableInfo:

    def __init__(self, top_headers: Set, left_headers: Set, td_map: Dict):
        """
        :param top_headers:
            {top_header, ...}
        :param left_headers:
            {left_header, ...}
        :param td_map:
            {
                top_header: {left_header: td_selector, ...}
            }
        """
        self._top_headers = top_headers
        self._left_headers = left_headers
        self._td_map = dict(td_map)

        self._init_check()

    def _init_check(self):
        for top in self._top_headers:
            for left in self._left_headers:
                td = self._td_map[top][left]
                assert isinstance(td, Selector)

    def get_td(self, top, left, td_extractor: BaseTdExtractor = None):
        if not td_extractor:
            td_extractor = FirstTextTdExtractor()

        try:
            td = self._td_map[top][left]
        except KeyError as err:
            raise HeaderMismatchError(repr(err))

        return td_extractor.extract(td=td)

    def has_header(self, top=None, left=None) -> bool:
        if top is None:
            return left in self._left_headers
        elif left is None:
            return top in self._top_headers
        else:
            return False


class BaseTableExtractor:

    def extract(self, table: Selector) -> TableInfo:
        raise NotImplementedError


class TopHeaderTableExtractor(BaseTableExtractor):

    def extract(self, table: Selector) -> TableInfo:
        top_header_list = []
        left_index_set = set()
        td_map = {}

        for th in table.css('thead th'):
            top_header = th.css('::text').get().strip()
            td_map[top_header] = {}
            top_header_list.append(top_header)

        for left_index, tr in enumerate(table.css('tbody tr')):
            left_index_set.add(left_index)

            for top_index, td in enumerate(tr.css('td')):
                top = top_header_list[top_index]
                td_map[top][left_index] = td

        return TableInfo(top_headers=set(top_header_list), left_headers=left_index_set, td_map=td_map)


class TopLeftHeaderTableExtractor(BaseTableExtractor):

    def extract(self, table: Selector) -> TableInfo:
        top_header_map = {}  # top_index: top_header
        left_header_set = set()
        td_map = {}

        for index, th in enumerate(table.css('thead th')):
            if index == 0:
                continue  # ignore top-left header

            top_header = th.css('::text').get().strip()
            top_header_map[index] = top_header
            td_map[top_header] = {}

        for tr in table.css('tbody tr'):
            td_list = list(tr.css('td'))

            left_header = td_list[0].css('::text').get().strip()
            left_header_set.add(left_header)

            for top_index, td in enumerate(td_list[1:], start=1):
                top = top_header_map[top_index]
                td_map[top][left_header] = td

        return TableInfo(top_headers=set(top_header_map.values()), left_headers=left_header_set, td_map=td_map)


class LeftHeaderTableExtractor(BaseTableExtractor):

    def extract(self, table: Selector) -> TableInfo:
        top_index_set = set()
        left_header_list = []
        td_map = {}

        for tr in table.css('tbody tr'):
            left_header = tr.css('th ::text').get().strip()
            left_header_list.append(left_header)

            for top_index, td in enumerate(tr.css('td')):
                top_index_set.add(top_index)
                td_dict = td_map.setdefault(top_index, {})
                td_dict[left_header] = td

        return TableInfo(top_headers=top_index_set, left_headers=set(left_header_list), td_map=td_map)
