from typing import List

from crawler.core_terminal.request_helpers import RequestOption


def verify(results: List):
    assert isinstance(results[0], RequestOption)
    assert "https://mct.tideworks.com/fc-MCT/import/default.do?method=container&eqptNbr=MEDU7322906" in results[0].url
    assert results[0].rule_name == 'CONTAINER_DETAIL'
