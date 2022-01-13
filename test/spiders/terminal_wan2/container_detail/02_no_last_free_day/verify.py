from crawler.core_terminal.items import TerminalItem


def verify(results):
    assert results[0] == TerminalItem(
        container_no="CAIU7902626",
        last_free_day=None,
        gate_out_date=None,
        vessel="MSC SAVONA",
        mbl_no="SMLMSHSR1D662400",
    )
