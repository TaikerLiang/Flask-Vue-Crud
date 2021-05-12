from crawler.core_terminal.items import TerminalItem


def verify(results):
    assert results[0] == TerminalItem(
        container_no='EISU9133920',
        freight_release='HOLD',
        customs_release='HOLD',
        discharge_date=None,
        ready_for_pick_up=False,
        appointment_date='No',
        last_free_day=None,
        gate_out_date=None,
        demurrage=None,
        carrier='EGL',
        container_spec='40/GP/96',
        holds='TMF',
        cy_location='V-LDER095W-141582',
        vessel='EVER LEADER',
        mbl_no='143076231631',
        weight='51831.0',
        hazardous='2.1:UN-1057',
    )
