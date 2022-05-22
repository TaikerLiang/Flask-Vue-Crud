from crawler.core_terminal.items import TerminalItem


def verify(results):
    assert results[0] == TerminalItem(
        container_no="BMOU4848347",
        last_free_day="Jan 14, 2022",
        vessel="OOCL LONDON",
        mbl_no="OOLU2683967840",
        available="Shipped",
    )
