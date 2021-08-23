from crawler.core_carrier.items import MblItem, ContainerItem, LocationItem, VesselItem, ContainerStatusItem


def verify(results):
    assert results[0] == MblItem(
        mbl_no='SSPHSEM8070851',
        por='',
        pol=LocationItem(name="SEMARANG, INDONESIA"),
        pod=LocationItem(name="NEW YORK (NY), U.S.A."),
        final_dest=LocationItem(name="NEW YORK (NY), U.S.A."),
        eta='03-Sep-2021',
    )

    assert results[1] == VesselItem(
        vessel_key='PELICAN',
        vessel='PELICAN',
        voyage='244 (PEI)',
        etd='21-Jul-2021',
        eta=None,
        pol=LocationItem(name="SEMARANG, INDONESIA"),
        pod=LocationItem(name=None),
    )

    assert results[2] == VesselItem(
        vessel_key=None,
        vessel=None,
        voyage=None,
        etd='04-Aug-2021',
        eta='03-Sep-2021',
        pol=LocationItem(name=None),
        pod=LocationItem(name='NEW YORK (NY), U.S.A.'),
    )

    assert results[3] == ContainerItem(
        container_key='TGHU1566474',
        container_no='TGHU1566474',
    )

    assert results[4] == ContainerStatusItem(
        container_key='TGHU1566474',
        description='Container was loaded at Transsihipment Port to Port of Discharge',
        local_date_time='04-Aug-2021',
        location=LocationItem(name='SINGAPORE, SINGAPORE'),
    )

    assert results[8] == ContainerStatusItem(
        container_key='TGHU1566474',
        description='Empty container dispatched from inland point to Customer',
        local_date_time='17-Jul-2021',
        location=LocationItem(name="SEMARANG, INDONESIA"),
    )
