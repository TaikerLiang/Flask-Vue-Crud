from crawler.core_terminal.items import TerminalItem


def verify(results):
    assert results[0] == TerminalItem(
        container_no='CBHU8755221',
        carrier_release='RELEASED',
        customs_release='RELEASED',
        discharge_date='10/08/21 22:45',
        ready_for_pick_up=False,
        appointment_date='No',
        last_free_day=None,
        gate_out_date='16/08/21 09:05',
        demurrage=None,
        carrier='COS',
        container_spec='40/GP/96',
        holds='',
        cy_location='COMMUNITY - OUT',
        vessel='APL DANUBE',
        mbl_no='6304246520',
        weight='16411',
        hazardous=None,
    )
