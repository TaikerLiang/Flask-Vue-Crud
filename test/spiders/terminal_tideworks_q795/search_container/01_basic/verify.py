from typing import List

from crawler.core_terminal.request_helpers import RequestOption


def verify(results: List):
    assert isinstance(results[0], RequestOption)
    assert "https://nol.tideworks.com/fc-NOL/import/default.do?method=container&eqptNbr=TRHU2178921" in results[0].url
    assert results[0].rule_name == "CONTAINER_DETAIL"
