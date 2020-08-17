from typing import List

from crawler.spiders.carrier_oolu import ForceRestart


def verify(results: List):
    assert isinstance(results[0], ForceRestart)

