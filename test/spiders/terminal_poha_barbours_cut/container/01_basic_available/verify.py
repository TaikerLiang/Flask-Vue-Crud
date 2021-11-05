from typing import List

from crawler.core_terminal.items import TerminalItem


def verify(results: List[TerminalItem]):
    assert results[0] == TerminalItem(
        available="Ready for Pick-up",
        container_no="EITU1692078",
        task_id=1,
        carrier="Evergreen Shipping Agency (America)(EGLV)",
        carrier_release="RELEASED",
        customs_release="RELEASED",
        holds="BILL OF LADING HOLD - LINE",
        container_spec="40GP96",
        weight="9502.0 KG",
    )
