from crawler.core_terminal.items import TerminalItem


def verify(results):
    assert results[0] == TerminalItem(
        container_no='EGHU9427104',
        freight_release='RELEASED',
        customs_release='RELEASED',
        discharge_date='06/05/20 01:09',
        ready_for_pick_up=True,
        appointment_date='08/05/20 00:00',
        last_free_day='11/05/20',
        gate_out_date=None,
        demurrage=None,
        carrier='EGL',
        container_spec='40/GP/96',
        holds=None,
        cy_location='Yard Grounded (G0770E3)',
        vessel='EVER LOVELY',
        mbl_no='142000398910',
        weight='22641.0',
        hazardous=None,
    )
