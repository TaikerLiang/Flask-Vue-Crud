import pytest
from scrapy.selector import Selector

from crawler.extractors.table_extractors import TableExtractor, TopLeftHeaderTableLocator, HeaderMismatchError


@pytest.fixture
def top_left_header_table_selector():
    return Selector(text="""
        <table>
            <thead>
                <tr>
                    <th></th>
                    <th>top1</th>
                    <th>top2</th>
                    <th>top3</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>left1</td>
                    <td>(1, 1)</td>
                    <td>(2, 1)</td>
                    <td>(3, 1)</td>
                </tr>
                <tr>
                    <td>left2</td>
                    <td>(1, 2)</td>
                    <td>(2, 2)</td>
                    <td>(3, 2)</td>
                </tr>
                <tr>
                    <td>left3</td>
                    <td>(1, 3)</td>
                    <td>(2, 3)</td>
                    <td>(3, 3)</td>
                </tr>
            </tbody>
        </table>
    """)


@pytest.mark.parametrize('top,left,expect', [
    ('top1', 'left1', '(1, 1)'),
    ('top1', 'left2', '(1, 2)'),
    ('top1', 'left3', '(1, 3)'),
    ('top2', 'left1', '(2, 1)'),
    ('top2', 'left2', '(2, 2)'),
    ('top2', 'left3', '(2, 3)'),
    ('top3', 'left1', '(3, 1)'),
    ('top3', 'left2', '(3, 2)'),
    ('top3', 'left3', '(3, 3)'),
])
def test_get_td(top, left, expect, top_left_header_table_selector):
    extractor = TableExtractor()
    table_info = extractor.extract(table=top_left_header_table_selector, locator=TopLeftHeaderTableLocator())

    result = table_info.extract_cell(top=top, left=left)
    assert result == expect


@pytest.mark.parametrize('top,left', [
    ('top1', 'NOT EXIST'),
    ('NOT EXIST', 'left1'),
])
def test_header_mismatch_error(top, left, top_left_header_table_selector):
    expect_exception = HeaderMismatchError

    extractor = TableExtractor()
    table_info = extractor.extract(table=top_left_header_table_selector, locator=TopLeftHeaderTableLocator())

    with pytest.raises(expect_exception):
        table_info.extract_cell(top=top, left=left)
