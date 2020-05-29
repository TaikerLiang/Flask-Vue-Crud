from crawler.core_terminal.items import TerminalItem


def verify(results):
    assert results[0] == TerminalItem(
        container_no='EMCU6085091',
        discharge_date='05/21/2020 8:53 PM',
        ready_for_pick_up='Off-dock',
        container_spec='20\' DRY CONTAINER',
        carrier='EGL',
        cy_location='OFFDOCK',
        vessel='CSCL YELLOW SEA',
        weight='20 MT',
        freight_release='PAID 05/19/2020 9:17 AM',
        customs_release='CLEARED 05/20/2020 4:20 PM',
        last_free_day='05/26/2020',
        demurrage='$0.00',
        holds='None',
    )