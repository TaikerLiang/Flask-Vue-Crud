from typing import List

from crawler.core_terminal.items import InvalidContainerNoItem


def verify(results: List):
    assert results[0] == InvalidContainerNoItem(
        task_id=1,
        container_no="QQQQQQQQQQQ",
    )
