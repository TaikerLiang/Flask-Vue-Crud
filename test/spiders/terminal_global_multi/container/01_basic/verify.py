from typing import List

from crawler.core_terminal.items import TerminalItem


def verify(results: List):
    assert results[0] == TerminalItem(
        container_no='KKFU7634200',
        freight_release='Yes',
        customs_release='Yes',
        discharge_date='02/09/2021',
        ready_for_pick_up='No',
        last_free_day='02/15/2021',
        gate_out_date='02/11/2021',
        demurrage='',
        carrier='ONE',
        container_spec='40-GP-96',
        vessel='HYUNDAI HOPE',
        voyage='042',
    )
