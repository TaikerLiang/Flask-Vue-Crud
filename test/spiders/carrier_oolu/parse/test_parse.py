import pytest

from crawler.spiders.carrier_oolu import CargoTrackingRule


@pytest.mark.parametrize('mbl_no_text,expect', [
    ('Search Result - Bill of Lading Number  2109051600 ', '2109051600'),
])
def test_parse_mbl_no_text(mbl_no_text, expect):
    result = CargoTrackingRule._parse_mbl_no_text(mbl_no_text=mbl_no_text)
    assert result == expect


@pytest.mark.parametrize('custom_release_info,expect', [
    (
        'Cleared (03 Nov 2019, 16:50 GMT)',
        ('Cleared', '03 Nov 2019, 16:50 GMT')),
    (
        'Not Applicable',
        ('Not Applicable', ''),
    )
])
def test_parse_custom_release_info(custom_release_info, expect):
    result = CargoTrackingRule._parse_custom_release_info(custom_release_info=custom_release_info)
    assert result == expect
