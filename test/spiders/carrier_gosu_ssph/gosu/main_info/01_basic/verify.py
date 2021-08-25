from crawler.core_carrier.items import MblItem, ContainerItem, LocationItem, VesselItem, ContainerStatusItem


def verify(results):
    assert results[0] == MblItem(
        mbl_no='GOSUGZH0147473',
        por='',
        pol=LocationItem(name="NANSHA (GD), CHINA. PEOPLE'S REPUBLIC"),
        pod=LocationItem(name="MELBOURNE (VI), AUSTRALIA"),
        final_dest=LocationItem(name="MELBOURNE (VI), AUSTRALIA"),
        eta='08-Aug-2021',
    )

    assert results[1] == VesselItem(
        vessel_key='NEW JERSEY TRADER',
        vessel='NEW JERSEY TRADER',
        voyage='11 (NJ1)',
        etd='23-Jul-2021',
        eta=None,
        pol=LocationItem(name="NANSHA (GD), CHINA. PEOPLE'S REPUBLIC"),
        pod=LocationItem(name=None),
    )

    assert results[2] == VesselItem(
        vessel_key=None,
        vessel=None,
        voyage=None,
        etd='23-Jul-2021',
        eta='08-Aug-2021',
        pol=LocationItem(name=None),
        pod=LocationItem(name='MELBOURNE (VI), AUSTRALIA'),
    )

    assert results[3] == ContainerItem(
        container_key='TEMU6346948',
        container_no='TEMU6346948',
    )

    assert results[4] == ContainerStatusItem(
        container_key='TEMU6346948',
        description='Empty container gate in',
        local_date_time='13-Aug-2021',
        location=LocationItem(name='MELBOURNE (VI), AUSTRALIA'),
    )

    assert results[9] == ContainerStatusItem(
        container_key='TEMU6346948',
        description='Empty container dispatched from inland point to Customer',
        local_date_time='04-Jul-2021',
        location=LocationItem(name="NANSHA (GD), CHINA. PEOPLE'S REPUBLIC"),
    )

    assert results[10] == ContainerItem(
        container_key='SEGU5433450',
        container_no='SEGU5433450',
    )

    assert results[17] == ContainerItem(
        container_key='CAIU8181761',
        container_no='CAIU8181761',
    )
