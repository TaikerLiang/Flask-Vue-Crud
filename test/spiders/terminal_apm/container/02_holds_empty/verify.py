from crawler.core_terminal.items import TerminalItem


def verify(results):
    assert results[0] == TerminalItem(
        container_no='EGHU9572519',
        freight_release='RELEASED',
        customs_release='RELEASED',
        discharge_date='29/04/20 09:45',
        ready_for_pick_up=False,
        appointment_date='30/04/20 13:00',
        last_free_day=None,
        gate_out_date='30/04/20 14:53',
        demurrage=None,
        carrier='EGL',
        container_spec='40/GP/96',
        holds=None,
        cy_location='COMMUNITY - OUT',
        vessel='EVER LUCENT',
        mbl_no='140027124903',
        weight='24956.0',
        hazardous=None,
    )
