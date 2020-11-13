from typing import List

from crawler.core_terminal.items import TerminalItem
from crawler.core_terminal.request_helpers import RequestOption


def verify(results: List):
    assert results[0] == TerminalItem(
        container_no='EGSU5003713',
        ready_for_pick_up='No',
        customs_release='Hold',
        appointment_date=None,
        last_free_day=None,
        demurrage=None,
        carrier='EGLV',
        container_spec="40'/Reefer/9'6\"",
        holds='No',
        cy_location=None,

        # extra field name
        service='Local Port/Door Cargo',
        carrier_release='Hold',
        tmf='Release',
        demurrage_status=None,

        # not on html
        freight_release='Hold',
    )

    assert isinstance(results[1], RequestOption)
    assert results[1].rule_name == 'MBL'
    assert results[1].form_data['PI_MFSMS_SYSNO'] == '16735758'







