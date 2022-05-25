from crawler.core_terminal.items import TerminalItem


def verify(results):
    assert results[0] == TerminalItem(
        container_no="MRSU3949609",
        discharge_date="08/22/2021 4:16 AM",
        ready_for_pick_up="Off-dock",
        available="Off-dock",
        container_spec="40' HIGH CUBE DRY CONTAINER",
        carrier="SUD",
        cy_location="OFFDOCK DEVN Block --, Row --, Stack --",
        yard_location="OFFDOCK DEVN Block --, Row --, Stack --",
        vessel="CAP SAN VINCENT",
        weight="6.1 MT",
        carrier_release="PAID",
        customs_release="CLEARED",
        last_free_day="08/27/2021",
        demurrage="$0.00",
        holds=None,
    )
