import pytest
from scrapy.selector import Selector

from crawler.extractors.table_extractors import TableExtractor, TopHeaderTableLocator, HeaderMismatchError


@pytest.fixture
def top_header_table_selector():
    return Selector(text="""
        <table>
            <thead>
                <tr>
                    <th>top1</th>
                    <th>top2</th>
                    <th>top3</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>(1, 1)</td>
                    <td>(2, 1)</td>
                    <td>(3, 1)</td>
                </tr>
                <tr>
                    <td>(1, 2)</td>
                    <td>(2, 2)</td>
                    <td>(3, 2)</td>
                </tr>
                <tr>
                    <td>(1, 3)</td>
                    <td>(2, 3)</td>
                    <td>(3, 3)</td>
                </tr>
            </tbody>
        </table>
    """)


@pytest.mark.parametrize('top,left,expect', [
    ('top1', 0, '(1, 1)'),
    ('top2', 0, '(2, 1)'),
    ('top3', 0, '(3, 1)'),
    ('top1', 1, '(1, 2)'),
    ('top2', 1, '(2, 2)'),
    ('top3', 1, '(3, 2)'),
    ('top1', 2, '(1, 3)'),
    ('top2', 2, '(2, 3)'),
    ('top3', 2, '(3, 3)'),
])
def test_get_td(top, left, expect, top_header_table_selector):
    locator = TopHeaderTableLocator()
    locator.parse(table=top_header_table_selector)
    extractor = TableExtractor(table_locator=locator)

    result = extractor.extract_cell(top=top, left=left)
    assert result == expect


@pytest.mark.parametrize('top,left', [
    ('top1', 4),
    ('top4', 0),
])
def test_header_mismatch_error(top, left, top_header_table_selector):
    expect_exception = HeaderMismatchError

    locator = TopHeaderTableLocator()
    locator.parse(table=top_header_table_selector)
    extractor = TableExtractor(table_locator=locator)

    with pytest.raises(expect_exception):
        extractor.extract_cell(top=top, left=left)
