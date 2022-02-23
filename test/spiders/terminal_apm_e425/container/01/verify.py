from crawler.core_terminal.items import TerminalItem


def verify(results):
    assert results[0] == TerminalItem(
        container_no="MRKU3570818",
        carrier_release="RELEASED",
        customs_release="RELEASED",
        discharge_date="02/08/21 10:57",
        ready_for_pick_up=False,
        appointment_date="No",
        last_free_day=None,
        gate_out_date="03/08/21 16:04",
        demurrage=None,
        carrier="SUD",
        container_spec="40/GP/96",
        holds="",
        cy_location="COMMUNITY - OUT",
        vessel="GUDRUN MAERSK",
        mbl_no="N1SHA053888X",
        weight="21914",
        hazardous=None,
    )
