from typing import List

from crawler.core_terminal.items import TerminalItem
from crawler.core_terminal.request_helpers import RequestOption


def verify(results: List):
    assert results[0] == TerminalItem(
        container_no='EMCU5268400',
        ready_for_pick_up='No',
        appointment_date='2020-08-10 00:00~',
        last_free_day='20200810',
        demurrage='0',
        carrier='EGLV',
        container_spec="40'/Reefer/9'6\"",
        holds='No',
        cy_location='Gate Out',
    )

    assert isinstance(results[1], RequestOption)
    assert results[1].rule_name == 'MBL'
    assert results[1].form_data['PI_MFSMS_SYSNO'] == '16701873'







