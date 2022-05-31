from crawler.core_terminal.items import TerminalItem


def verify(results):
    assert results[0] == TerminalItem(
        container_no="SEGU5842736",
        carrier_release="RELEASED",
        customs_release="RELEASED",
        discharge_date="15/08/21 15:59",
        ready_for_pick_up=False,
        available=False,
        appointment_date="No",
        last_free_day="19/08/21",
        gate_out_date=None,
        demurrage=None,
        carrier="EGL",
        container_spec="40/GP/96",
        holds="TMF",
        cy_location="Yard Grounded (H0784A2)",
        yard_location="Yard Grounded (H0784A2)",
        vessel="EVER LAMBENT",
        mbl_no="143155243314",
        weight="26015.0",
        hazardous=None,
    )
