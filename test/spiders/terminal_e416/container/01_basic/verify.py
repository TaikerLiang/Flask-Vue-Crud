from crawler.core_terminal.items import TerminalItem


def verify(results):
    assert results[0] == TerminalItem(
        container_no='EISU9407701',
        container_spec="40' 9'6\" Dry",
        available='No',
        customs_release='Released',
        discharge_date='',
        last_free_day='',
        carrier_release='Yes',
    )