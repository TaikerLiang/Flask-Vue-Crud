from typing import List

from crawler.core_terminal.items import TerminalItem


def verify(results: List):
    assert results[0] == TerminalItem(
        container_no='MRKU7463470',
        container_spec='Standard 20\' 8\'6"',
        customs_release='Released',
        cy_location='DD5-543-C-3(Deck)',
        ready_for_pick_up='Yes',
        appointment_date='09-02-2021 13:00~14:00',
        carrier_release='Released',
        holds='',
        last_free_day='09-01-2021',
    )
