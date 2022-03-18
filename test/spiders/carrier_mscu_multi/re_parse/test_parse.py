import pytest

from crawler.core.base_new import SEARCH_TYPE_MBL
from crawler.spiders.carrier_mscu_multi import Extractor


@pytest.mark.parametrize(
    "container_no_text,expect,task_id",
    [
        ("Container: GLDU7636572", "GLDU7636572", "1"),
    ],
)
def test_parse_container_no(container_no_text, expect, task_id):
    info_pack = {
        "search_type": SEARCH_TYPE_MBL,
        "search_no": expect,
        "task_id": task_id,
    }
    extractor = Extractor(info_pack=info_pack)
    result = extractor._parse_container_no(container_no_text=container_no_text)
    assert result == expect


@pytest.mark.parametrize(
    "latest_update_message,expect,task_id",
    [
        (
            "Tracking results provided by MSC on 05.11.2019 at 10:50 W. Europe Standard Time",
            "05.11.2019 at 10:50 W. Europe Standard Time",
            "1",
        ),
    ],
)
def test_parse_latest_update(latest_update_message, expect, task_id):
    info_pack = {
        "search_type": SEARCH_TYPE_MBL,
        "search_no": expect,
        "task_id": task_id,
    }
    extractor = Extractor(info_pack=info_pack)
    result = extractor._parse_latest_update(latest_update_message=latest_update_message)
    assert result == expect
