from crawler.core_terminal.items import TerminalItem


def verify(results):
    assert results[0] == TerminalItem(
        container_no='FCIU3460294',
        carrier_release='RELEASED',
        customs_release='RELEASED',
        discharge_date='03/08/21 13:21',
        ready_for_pick_up=False,
        appointment_date='04/08/21 12:00',
        last_free_day=None,
        gate_out_date='04/08/21 14:09',
        demurrage=None,
        carrier='CMA',
        container_spec='20/GP/86',
        holds='',
        cy_location='COMMUNITY - OUT',
        vessel='APL DANUBE',
        mbl_no='CNBW909554',
        weight='50750.0',
        hazardous=None,
    )
