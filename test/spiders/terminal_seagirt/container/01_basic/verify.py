from crawler.core_terminal.items import TerminalItem


def verify(results):
    assert results[0] == TerminalItem(
        container_no='DRYU2659319',
        carrier_release='RELEASED',
        customs_release='RELEASED',
        discharge_date='2021-10-31T16:56:45.555',
        ready_for_pick_up='Yes',
        last_free_day='2021-11-04T00:00:00',
        demurrage=0.0,
        carrier='EIS',
        container_spec="20'/VH/8'6",
        holds=0,
        vessel='EVFT',
        voyage='1112',
        mbl_no='143100507352',
        weight=23200.0,
        demurrage_status='R',
    )
