from crawler.core_terminal.items import TerminalItem


def verify(results):
    assert results[0] == TerminalItem(
        container_no="KOCU4471983",
        carrier_release="RELEASED",
        customs_release="RELEASED",
        discharge_date="15/08/21 15:52",
        ready_for_pick_up=True,
        available=True,
        appointment_date="No",
        last_free_day="19/08/21",
        gate_out_date=None,
        demurrage=None,
        carrier="HMM",
        container_spec="40/GP/96",
        holds="",
        cy_location="Yard Grounded (21724A3)",
        yard_location="Yard Grounded (21724A3)",
        vessel="ONE MAXIM",
        mbl_no="NBOZ33498300",
        weight="40682.0",
        hazardous=None,
    )
