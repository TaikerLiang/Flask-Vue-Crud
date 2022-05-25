from crawler.core_terminal.items import TerminalItem


def verify(results):
    assert results[0] == TerminalItem(
        container_no="MSDU8048551",
        discharge_date="07/26/2021 10:11 AM",
        ready_for_pick_up="Off-dock",
        available="Off-dock",
        container_spec="40' HIGH CUBE DRY CONTAINER",
        carrier="MSC",
        cy_location="OFFDOCK FCL Block --, Row --, Stack --",
        yard_location="OFFDOCK FCL Block --, Row --, Stack --",
        vessel="MSC AQUARIUS",
        weight="17.8 MT",
        carrier_release="PAID",
        customs_release="CLEARED",
        last_free_day="07/30/2021",
        demurrage="",
        holds=None,
    )
