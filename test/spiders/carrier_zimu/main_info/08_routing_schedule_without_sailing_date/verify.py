from crawler.core_carrier.items import MblItem, LocationItem, VesselItem, ContainerItem, ContainerStatusItem


def verify(results):
    assert results[0] == VesselItem(
        vessel_key=0,
        vessel='MSC LONDON',
        voyage='6',
        pol=LocationItem(name="NINGBO (ZJ), CHINA. PEOPLE'S REPUBLIC"),
        pod=LocationItem(name="PIRAEUS, GREECE"),
        etd='01-Apr-2020',
        eta='03-May-2020',
    )

    assert results[1] == MblItem(
        mbl_no='ZIMUNGB9491892',
        vessel=None,
        voyage=None,
        por=LocationItem(name=None),
        pol=LocationItem(name="NINGBO (ZJ), CHINA. PEOPLE'S REPUBLIC"),
        pod=LocationItem(name='DURRES, ALBANIA'),
        final_dest=LocationItem(un_lo_code=None, name=None),
        etd='01-Apr-2020',
        eta='08-May-2020',
        deliv_eta=None,
    )

    assert results[2] == ContainerItem(
        container_key='FCIU4134820',
        container_no='FCIU4134820',
    )

    assert results[3] == ContainerStatusItem(
        container_key='FCIU4134820',
        description='Export gate-in from Customer to Port of Loading',
        local_date_time='28-Mar-2020 12:11',
        location=LocationItem(name="NINGBO (ZJ), CHINA. PEOPLE'S REPUBLIC")
    )

