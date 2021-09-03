from crawler.core_terminal.items import TerminalItem


def verify(results):
    assert results[0] == TerminalItem(
        container_no='CCLU7014409',
        ready_for_pick_up='Yes (TMF Rlsd)',
        gate_out_date='In Yard BB9-924-M3(D)',
        appointment_date='',
        customs_release='Released',
        carrier_release='Released',
        holds='None',
        demurrage='',
        last_free_day='8/26/2021',
        carrier='COSCO',
        container_spec='Standard',
    )
