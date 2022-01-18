from crawler.core_terminal.items import TerminalItem


def verify(results):
    assert results[0] == TerminalItem(
        container_no="OTPU6344278",
        last_free_day="11/16/21",
        vessel="MATSON HAWAII",
        mbl_no="MATS9541127000",
    )
