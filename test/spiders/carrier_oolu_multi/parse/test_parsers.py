import pytest

from crawler.core.base import SEARCH_TYPE_MBL
from crawler.spiders.carrier_oolu_multi import CargoTrackingRule


@pytest.mark.parametrize(
    "search_no_text,expect",
    [
        ("Search Result - Bill of Lading Number  2109051600 ", "2109051600"),
        ("Search Result - Booking Number  2109052988 ", "2109052988"),
    ],
)
def test_parse_mbl_no_text(search_no_text, expect):
    info_pack = {
        "task_id": "1",
        "search_no": "",
        "search_type": SEARCH_TYPE_MBL,
    }
    result = CargoTrackingRule._parse_search_no_text(search_no_text=search_no_text, info_pack=info_pack)

    assert result == expect


@pytest.mark.parametrize(
    "custom_release_info,expect",
    [
        ("Cleared (03 Nov 2019, 16:50 GMT)", ("Cleared", "03 Nov 2019, 16:50 GMT")),
        (
            "Not Applicable",
            ("Not Applicable", ""),
        ),
    ],
)
def test_parse_custom_release_info(custom_release_info, expect):
    info_pack = {
        "task_id": "1",
        "search_no": "",
        "search_type": SEARCH_TYPE_MBL,
    }
    result = CargoTrackingRule._parse_custom_release_info(custom_release_info=custom_release_info, info_pack=info_pack)
    assert result == expect
