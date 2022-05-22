from crawler.core_terminal.items import TerminalItem, ExportErrorData
from crawler.core_terminal.rules import RequestOption


def verify(results):
    # arrange
    answers = {
        "ECMU8065005": TerminalItem(
            container_no="ECMU8065005",
            available="No",
            customs_release="Released",
            discharge_date="2022-JAN-26 17:18:33",
            last_free_day="2022-Feb-01",
            carrier_release="Yes",
        ),
        "UETU5115112": TerminalItem(
            container_no="UETU5115112",
            available="No",
            customs_release="Released",
            discharge_date="2022-JAN-24 18:45:23",
            last_free_day="2022-Jan-28",
            carrier_release="No",
        ),
        "APHU7007894": ExportErrorData(
            container_no="APHU7007894",
            detail="Data was not found",
            status="ERROR",
        ),
        "TRHU6046630": TerminalItem(
            container_no="TRHU6046630",
            available="No",
            customs_release="Released",
            discharge_date="2022-JAN-24 17:46:31",
            last_free_day="2022-Jan-28",
            carrier_release="No",
        ),
        "OOLU6811996": TerminalItem(
            container_no="OOLU6811996",
            available="No",
            customs_release="Released",
            discharge_date="2022-JAN-24 20:10:15",
            last_free_day="2022-Jan-28",
            carrier_release="No",
        ),
    }

    # assert
    from pprint import pprint

    pprint(results)

    for result in results:
        if isinstance(result, RequestOption):
            continue
        assert result == answers[result["container_no"]]
