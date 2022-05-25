from crawler.core_terminal.items import TerminalItem


def verify(results):
    assert results[0] == TerminalItem(
        container_no="UACU5946066",
        carrier_release="RELEASED",
        customs_release="RELEASED",
        discharge_date="02/08/21 16:15",
        ready_for_pick_up=False,
        available=False,
        appointment_date="04/08/21 08:00",
        last_free_day=None,
        gate_out_date="04/08/21 10:42",
        demurrage=None,
        carrier="HLC",
        container_spec="40/GP/96",
        holds="",
        cy_location="COMMUNITY - OUT",
        yard_location="COMMUNITY - OUT",
        vessel="ONE MANEUVER",
        mbl_no="SHA2105BWVF9",
        weight="50265.0",
        hazardous=None,
    )
