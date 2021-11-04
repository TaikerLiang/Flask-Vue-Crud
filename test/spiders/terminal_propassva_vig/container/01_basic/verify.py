from typing import List

from crawler.core_terminal.items import TerminalItem


def verify(results: List):
    assert results[0] == TerminalItem(
        available="ON VESSEL",
        container_no="EITU3044650",
        customs_release="",
        demurrage="",
        gate_out_date="",
        holds=[
            {
                "HoldCode": "QQ",
                "HoldDescription": "CUSTOMS Default Bill Hold ",
                "HoldDate": "2021-10-28T00:05:00-04:00",
                "sHoldDtTm": "28 Oct 2021 00:05",
                "txtHoldDate": "2021-10-28T00:05:00-04:00",
            }
        ],
        last_free_day=None,
        vessel="THALASSA DOXA",
        voyage="THDO-1113W",
    )
    assert results[1] == TerminalItem(
        available="AVAILABLE",
        container_no="BMOU4520471",
        customs_release="RELEASED",
        demurrage="",
        gate_out_date="",
        holds=[],
        last_free_day=None,
        vessel="GRETE MAERSK",
        voyage="GRMA-140W",
    )
    assert results[2] == TerminalItem(
        available="AVAILABLE",
        container_no="MEDU8348187",
        customs_release="RELEASED",
        demurrage="",
        gate_out_date="",
        holds=[],
        last_free_day=None,
        vessel="MSC NAOMI",
        voyage="NAOM-IV142R",
    )
    assert results[3] == TerminalItem(
        available="OUT-GATE",
        container_no="TCKU4811590",
        customs_release="",
        demurrage="",
        gate_out_date="2021-10-26T16:08:00-04:00",
        holds=[],
        last_free_day=None,
        vessel="MEISHAN BRIDGE",
        voyage="015E",
    )
    assert results[4] == TerminalItem(
        available="NOT AVAILABLE",
        container_no="OOCU7493403",
        customs_release="RELEASED",
        demurrage="",
        gate_out_date="",
        holds=[],
        last_free_day=None,
        vessel="CMA CGM MARCO POLO",
        voyage="POLO-0TUKEN1",
    )
