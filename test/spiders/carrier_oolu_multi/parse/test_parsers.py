import pytest

from crawler.spiders.carrier_oolu_multi import CargoTrackingRule


@pytest.mark.parametrize('search_no_text,expect', [
    ('Search Result - Bill of Lading Number  2109051600 ', '2109051600'),
    ('Search Result - Booking Number  2109052988 ', '2109052988'),
])
def test_parse_mbl_no_text(search_no_text, expect):
    result = CargoTrackingRule._parse_search_no_text(search_no_text=search_no_text)
 
    assert result == expect


@pytest.mark.parametrize(
    'custom_release_info,expect',
    [
        ('Cleared (03 Nov 2019, 16:50 GMT)', ('Cleared', '03 Nov 2019, 16:50 GMT')),
        (
            'Not Applicable',
            ('Not Applicable', ''),
        ),
    ],
)
def test_parse_custom_release_info(custom_release_info, expect):
    result = CargoTrackingRule._parse_custom_release_info(custom_release_info=custom_release_info)
    assert result == expect