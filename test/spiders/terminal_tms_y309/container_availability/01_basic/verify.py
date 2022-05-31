from crawler.core_terminal.items import TerminalItem


def verify(results):
    assert results[0] == TerminalItem(
        available="Not Available",
        container_no="TGHU0113128",
        carrier_release="OK",
        customs_release="OK",
        appointment_date="08/12/2021",
        ready_for_pick_up="Not Available",
        last_free_day="08/17/2021",
        demurrage="",
        carrier="HAP",
        container_spec="20DR86",
        vessel="YM WHOLESOME",
        mbl_no="CA4210570233",
        voyage="028E",
        gate_out_date="DELIVERED 08/18/2021",
        chassis_no="CTSZ007",
    )
