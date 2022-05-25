from crawler.core_terminal.items import TerminalItem


def verify(results):
    assert results[0] == TerminalItem(
        container_no="TEMU2925237",
        carrier_release="RELEASED",
        customs_release="RELEASED",
        discharge_date="12/08/21 23:25",
        ready_for_pick_up=True,
        available=True,
        appointment_date="No",
        last_free_day="18/08/21",
        gate_out_date=None,
        demurrage=None,
        carrier="CMA",
        container_spec="20/GP/86",
        holds="",
        cy_location="Yard Grounded (4H05B4)",
        yard_location="Yard Grounded (4H05B4)",
        vessel="GULF BRIDGE",
        mbl_no="NBPC016685B",
        weight="17569",
        hazardous=None,
    )
