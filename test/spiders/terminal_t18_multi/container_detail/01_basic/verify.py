
from crawler.core_terminal.items import TerminalItem


def verify(results):
    assert results[0] == TerminalItem(
        container_no='CCLU7849100',
        discharge_date='07/31/2021 8:14 PM',
        ready_for_pick_up='Not available',
        container_spec='40\' HIGH CUBE DRY CONTAINER',
        carrier='OOL',
        cy_location='YARD V12C Block V1, Row 12, Stack C',
        vessel='CMA CGM PELLEAS',
        weight='13.8 MT',
        carrier_release='HELD',
        customs_release='CLEARED',
        last_free_day='08/17/2021',
        demurrage='$531.60',
        holds=None,
    )