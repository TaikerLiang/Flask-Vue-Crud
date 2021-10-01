from crawler.core_terminal.items import TerminalItem


def verify(results):
    assert results[0] == TerminalItem(
        container_no='CSNU7920778',
        container_spec="40' 9'6\" Dry",
        available='Yes',
        customs_release='Released',
        discharge_date='2021-08-18T03:59:44 -0400',
        last_free_day='08.23.2021',
        carrier_release='Yes',
    )