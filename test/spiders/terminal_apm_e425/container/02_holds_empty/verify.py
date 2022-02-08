from crawler.core_terminal.items import TerminalItem


def verify(results):
    assert results[0] == TerminalItem(
        container_no="GCXU5805042",
        carrier_release="RELEASED",
        customs_release="RELEASED",
        discharge_date="30/07/21 14:17",
        ready_for_pick_up=False,
        appointment_date="02/08/21 09:00",
        last_free_day=None,
        gate_out_date="02/08/21 10:50",
        demurrage=None,
        carrier="SUD",
        container_spec="40/GP/96",
        holds="",
        cy_location="COMMUNITY - OUT",
        vessel="PAXI",
        mbl_no="N1KSZ057110X",
        weight="58257",
        hazardous=None,
    )
