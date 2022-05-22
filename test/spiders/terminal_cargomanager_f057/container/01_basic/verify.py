from crawler.core_terminal.items import TerminalItem


def verify(results):
    assert results[0] == TerminalItem(
        container_no="FCIU9186874",
        last_free_day="Aug 3, 2021",
        vessel="COSCO DEVELOPMENT",
        mbl_no="EGLV142154311890",
        available="Shipped",
    )
