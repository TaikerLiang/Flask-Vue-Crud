from crawler.core_terminal.items import TerminalItem


def verify(results):
    assert results[0] == TerminalItem(
        container_no='NYKU4410168',
        freight_release='OK',
        customs_release='OK',
        discharge_date='04/09/2020',
        ready_for_pick_up='Not Available',
        last_free_day='04/15/2020',
        demurrage='',
        carrier='ONE',
        container_spec='40DR96',
        vessel='MOL CELEBRATION',
        mbl_no='SH9ER3047500',
        voyage='076E',
        chassis_no='FB',
    )
