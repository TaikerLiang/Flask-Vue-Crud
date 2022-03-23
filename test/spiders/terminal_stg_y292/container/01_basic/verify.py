from crawler.core_terminal.items import TerminalItem


def verify(results):
    assert results[0] == TerminalItem(
        container_no="OOLU9879270",
        mbl_no="COSU6323480660",
        available="On Vessel",
        vessel="CMA CGM A. LINCOLN",
        appointment_date="",
    )
