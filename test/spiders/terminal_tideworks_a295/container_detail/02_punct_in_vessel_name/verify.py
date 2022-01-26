from crawler.core_terminal.items import TerminalItem


def verify(results):
    assert results[0] == TerminalItem(
        container_no="MSDU7655308",
        discharge_date="01/23/2022 10:18 PM",
        ready_for_pick_up="Available",
        container_spec="40' HIGH CUBE DRY CONTAINER",
        carrier="MSC",
        cy_location="YARD",
        vessel="MSC VAISHNAVI R.",
        weight="19 MT",
        carrier_release="PAID",
        customs_release="CLEARED",
        last_free_day="01/30/2022",
        demurrage="",
        holds=None,
    )
