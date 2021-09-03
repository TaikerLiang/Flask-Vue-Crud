from typing import List

from crawler.core_terminal.items import TerminalItem


def verify(results: List):
    assert results[0] == TerminalItem(
        container_no='KKFU7634200',
        carrier_release='Yes',
        customs_release='Yes',
        ready_for_pick_up='No',
        discharge_date='02/09/2021',
        last_free_day='02/15/2021',
        gate_out_date='02/11/2021',
    )
