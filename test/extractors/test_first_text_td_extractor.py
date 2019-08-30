from scrapy import Selector

from crawler.extractors.table_cell_extractors import FirstTextTdExtractor


class TestFirstTextTdExtractor:

    def test_extract(self):
        expect = 'This is test for td::text'

        # arrange
        td_selector = Selector(text='<td>  This is test for td::text  </td>')
        td_extractor = FirstTextTdExtractor()

        # action
        result = td_extractor.extract(cell=td_selector)

        # assert
        assert result == expect

    def test_extract_with_css_query(self):
        expect = 'This is test for td a::text'

        # arrange
        td_selector = Selector(text="""
            <td>
                <a>  This is test for td a::text  </a>
            </td>
        """)

        css_query = 'a::text'
        td_extractor = FirstTextTdExtractor(css_query=css_query)

        # action
        result = td_extractor.extract(cell=td_selector)

        # assert
        assert result == expect
