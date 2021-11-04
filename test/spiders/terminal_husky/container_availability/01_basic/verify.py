from crawler.core_terminal.items import TerminalItem


def verify(results):
    assert results[0] == TerminalItem(
        container_no='MSMU5136043',
        carrier_release='OK',
        customs_release='OK',
        appointment_date='08/18 1st shift',
        ready_for_pick_up='Not Available',
        last_free_day='',
        demurrage='',
        carrier='MSC',
        container_spec='40DR96',
        vessel='MSC POH LIN',
        mbl_no='CP182917',
        voyage='126N',
        gate_out_date='ARRIVING 08/18 1st shift',
        chassis_no='',
    )
