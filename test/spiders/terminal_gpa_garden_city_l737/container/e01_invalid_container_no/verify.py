from typing import List, Dict

from crawler.core_terminal.items import InvalidContainerNoItem


def verify(results: List[Dict]):
    assert len(results) == 1
    assert results[0] == InvalidContainerNoItem(
        container_no=["QQQQQQQQQQQQ"],
    )
