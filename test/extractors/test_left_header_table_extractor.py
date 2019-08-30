import pytest
from scrapy.selector import Selector

from crawler.extractors.table_extractors import TableExtractor, LeftHeaderTableLocator, HeaderMismatchError


@pytest.fixture
def left_header_table_selector():
    return Selector(text="""
        <table>
            <tbody>
                <tr>
                    <th>left1</th>
                    <td>(1, 1)</td>
                    <td>(2, 1)</td>
                    <td>(3, 1)</td>
                </tr>
        
                <tr>                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        
                    <th>left2</th>
                    <td>(1, 2)</td>
                    <td>(2, 2)</td>
                    <td>(3, 2)</td>
                </tr>
        
                <tr>
                    <th>left3</th>
                    <td>(1, 3)</td>
                    <td>(2, 3)</td>
                    <td>(3, 3)</td>
                </tr>
            </tbody>
        </table>
    """)


@pytest.mark.parametrize('top,left,expect', [
    (0, 'left1', '(1, 1)'),
    (0, 'left2', '(1, 2)'),
    (0, 'left3', '(1, 3)'),
    (1, 'left1', '(2, 1)'),
    (1, 'left2', '(2, 2)'),
    (1, 'left3', '(2, 3)'),
    (2, 'left1', '(3, 1)'),
    (2, 'left2', '(3, 2)'),
    (2, 'left3', '(3, 3)'),
])
def test_get_td(top, left, expect, left_header_table_selector):
    extractor = TableExtractor()
    table_info = extractor.extract(table=left_header_table_selector, locator=LeftHeaderTableLocator())
    result = table_info.extract_cell(top=top, left=left)
    assert result == expect


@pytest.mark.parametrize('top,left', [
    (0, 'left4'),
    (3, 'left1'),
])
def test_header_mismatch_error(top, left, left_header_table_selector):
    expect_exception = HeaderMismatchError

    extractor = TableExtractor()
    table_info = extractor.extract(table=left_header_table_selector, locator=LeftHeaderTableLocator())

    with pytest.raises(expect_exception):
        table_info.extract_cell(top=top, left=left)
