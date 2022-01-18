from crawler.core_terminal.items import TerminalItem


def verify(results):
    assert results[0] == TerminalItem(
        container_no="TWCU8058905",
        last_free_day=None,
        vessel="AS SERAFINA",
        mbl_no="SJBVASHLB100122",
    )
