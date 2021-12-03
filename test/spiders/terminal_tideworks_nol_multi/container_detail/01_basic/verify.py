from crawler.core_terminal.items import TerminalItem


def verify(results):
    assert results[0] == TerminalItem(
        container_no="TRHU2178921",
        discharge_date="11/22/2021 7:32 PM",
        ready_for_pick_up="Off-dock",
        container_spec="20' DRY CONTAINER",
        carrier="MSC",
        cy_location="OFFDOCK TBD TCIO Block --, Row --, Stack --",
        vessel="MAERSK SEVILLE",
        weight="24.2 MT",
        carrier_release="PAID",
        customs_release="CLEARED",
        last_free_day="",
        demurrage="",
        holds=None,
    )
