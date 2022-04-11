from crawler.core_terminal.items import TerminalItem


def verify(results):
    assert results[0] == TerminalItem(
        container_no="GCXU5015109",
        last_free_day="Mar 28, 2022",
        vessel="ONE MATRIX",
        mbl_no="HDMUNBOZ39417700",
        available="Available",
    )
