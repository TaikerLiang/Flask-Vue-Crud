from typing import List

from crawler.core_terminal.items import DebugItem
from crawler.core_terminal.request_helpers import RequestOption


def verify(results: List):
    assert isinstance(results[0], DebugItem)
    assert isinstance(results[1], RequestOption)
    assert results[1].rule_name == "CONTAINER"
    assert results[1].meta["container_no_list"] == ["EITU1162062/"]
    assert isinstance(results[2], RequestOption)
    assert results[2].rule_name == "CONTAINER"
    assert results[2].meta["container_no_list"] == ["EITU1162062"]
    assert isinstance(results[3], RequestOption)
    assert results[3].rule_name == "NEXT_ROUND"
