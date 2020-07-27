from typing import List

from crawler.spiders.carrier_ymlu import Restart


def verify(results: List):
    assert isinstance(results[0], Restart)

