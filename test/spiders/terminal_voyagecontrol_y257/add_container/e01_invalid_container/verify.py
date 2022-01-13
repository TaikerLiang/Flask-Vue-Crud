from typing import List

from crawler.core_terminal.items import InvalidContainerNoItem

def verify(results: List):
    assert isinstance(results[0], InvalidContainerNoItem)