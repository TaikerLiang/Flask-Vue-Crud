from crawler.core_terminal.items import TerminalItem


def verify(results):
    assert results[0] == TerminalItem(
        container_no="TCNU1654552",
        carrier_release="RELEASED",
        customs_release="RELEASED",
        discharge_date=None,
        ready_for_pick_up=False,
        available=False,
        appointment_date="No",
        last_free_day=None,
        gate_out_date=None,
        demurrage=None,
        carrier="EGL",
        container_spec="40/GP/96",
        holds="",
        cy_location="V-EVEL0969W-740112",
        yard_location="V-EVEL0969W-740112",
        vessel="EVER LAMBENT",
        mbl_no="143161057501",
        weight="33091.0",
        hazardous=None,
    )
