
from crawler.core_terminal.items import TerminalItem


def verify(results):
    assert results[0] == TerminalItem(
        container_no='MEDU7322906',
        discharge_date='10/25/2021 1:49 PM',
        ready_for_pick_up='Off-dock',
        container_spec='40\' HIGH CUBE DRY CONTAINER',
        carrier='MSC',
        cy_location='OFFDOCK',
        vessel='MSC PAMELA',
        weight='16.9 MT',
        carrier_release='PAID',
        customs_release='CLEARED',
        last_free_day='11/01/2021',
        demurrage='',
        holds=None,
    )