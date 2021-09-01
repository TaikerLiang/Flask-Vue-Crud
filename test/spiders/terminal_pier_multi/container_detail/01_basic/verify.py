from crawler.core_terminal.items import TerminalItem


def verify(results):
    assert results[0] == TerminalItem(
        container_no='WHSU6189984',
        discharge_date='08/07/2021 1:28 PM',
        ready_for_pick_up='Off-dock',
        container_spec='40\' HIGH CUBE DRY CONTAINER',
        carrier='WHL',
        cy_location='OFFDOCK',
        vessel='WAN HAI 313',
        weight='13.4 MT',
        carrier_release='PAID',
        customs_release='CLEARED',
        last_free_day='08/12/2021',
        demurrage='$0.00',
        holds=None,
    )
