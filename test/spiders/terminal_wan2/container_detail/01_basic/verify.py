from crawler.core_terminal.items import TerminalItem


def verify(results):
    assert results[0] == TerminalItem(
        container_no="MATU4547183",
        last_free_day="Nov 23, 2021",
        gate_out_date="Dec 1, 2021",
        vessel="MATSONIA",
        mbl_no="MATS5120186000",
    )
