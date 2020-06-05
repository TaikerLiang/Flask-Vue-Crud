from crawler.core_terminal.items import TerminalItem


def verify(results):
    assert results[0] == TerminalItem(
        container_no='TGBU678745-5',
        freight_release='Released',
        customs_release='Released',
        ready_for_pick_up=None,
        appointment_date=None,
        last_free_day='6/3/2020',
        demurrage=None,
        carrier='Yang Ming',
        container_spec='Standard',
        holds='None',
    )
