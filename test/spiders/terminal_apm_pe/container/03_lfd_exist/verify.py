from crawler.core_terminal.items import TerminalItem


def verify(results):
    assert results[0] == TerminalItem(
        container_no='TGCU5024679',
        carrier_release='RELEASED',
        customs_release='RELEASED',
        discharge_date='11/08/21 08:07',
        ready_for_pick_up=True,
        appointment_date='17/08/21 06:00',
        last_free_day='17/08/21',
        gate_out_date=None,
        demurrage=None,
        carrier='MSC',
        container_spec='40/GP/96',
        holds='',
        cy_location='Yard Grounded (G40518C4)',
        vessel='YORK',
        mbl_no='CF318116',
        weight='15512',
        hazardous=None,
    )
