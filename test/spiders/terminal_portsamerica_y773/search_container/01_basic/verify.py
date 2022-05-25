from crawler.core_terminal.items import TerminalItem


def verify(results):
    assert results[0] == TerminalItem(
        container_no="ZCSU8739851",
        ready_for_pick_up="No (TMF Hold)",
        available="No",
        gate_out_date="On Ship",
        appointment_date="",
        customs_release="No Status",
        carrier_release="Released",
        holds="None",
        demurrage="",
        last_free_day="",
        carrier="ZIM",
        container_spec="Standard",
        yard_location="On Ship",
    )
