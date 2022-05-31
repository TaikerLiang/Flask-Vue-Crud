from crawler.core_terminal.items import TerminalItem


def verify(results):
    assert results[0] == TerminalItem(
        container_no="EISU9112296",
        carrier_release="RELEASED",
        customs_release="RELEASED",
        discharge_date="14/08/21 09:23",
        ready_for_pick_up=True,
        available=True,
        appointment_date="No",
        last_free_day="19/08/21",
        gate_out_date=None,
        demurrage=None,
        carrier="EGL",
        container_spec="40/GP/96",
        holds="",
        cy_location="Yard Wheeled (61737)",
        yard_location="Yard Wheeled (61737)",
        vessel="EVER LAMBENT",
        mbl_no="143165715570",
        weight="28131.0",
        hazardous=None,
    )
