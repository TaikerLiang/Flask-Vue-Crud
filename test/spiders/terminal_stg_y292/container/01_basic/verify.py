from crawler.core_terminal.items import TerminalItem


def verify(results):
    assert results[0] == TerminalItem(
        container_no="OOLU9879270",
        mbl_no="COSU6323480660",
        ready_for_pick_up="On Vessel",
        vessel="CMA CGM A. LINCOLN",
        last_free_day=None,
        appointment_date="",
        gate_out_date="",
    )
