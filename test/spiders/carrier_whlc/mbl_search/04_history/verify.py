from typing import List


def verify(results: List):
    assert results[0] == (
        {
            "description": "Full container(FCL) discharged from vessel OR GATE IN to Pier/Terminal",
            "local_date_time": "2021/08/21 07:00",
            "location_name": "Oakland International Container Terminal; OICT (Berth 57-59) ; SSA Marine",
        }
    )

    assert results[1] == (
        {
            "description": "LADEN CTNR LOADED ON BOARD VESSEL.(MOTHER VESSEL,FIXED SLOT CHARTER/JOINT VENTURE VESSEL)",
            "local_date_time": "2021/08/02 02:48",
            "location_name": "NINGBO BEILUN INTL CTNR TERMIANL LTD.",
        }
    )

    assert results[2] == (
        {
            "description": "OUTBOUND FULL CONTAINER GATE IN TO PEIR/TERMINAL(FCL)",
            "local_date_time": "2021/07/28 18:52",
            "location_name": "NINGBO BEILUN INTL CTNR TERMIANL LTD.",
        }
    )
