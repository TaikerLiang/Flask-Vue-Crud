from crawler.core_carrier.items import MblItem, LocationItem, ContainerItem, ContainerStatusItem, VesselItem


def verify(results):
    assert results[0] == VesselItem(
        vessel_key=0,
        vessel='CAPE TAINARO',
        voyage='3',
        pol=LocationItem(name="SHANGHAI (SH), CHINA. PEOPLE'S REPUBLIC"),
        pod=LocationItem(name='SAVANNAH (GA), U.S.A.'),
        etd='17-Oct-2019',
        eta='13-Nov-2019',
    )
    assert results[1] == MblItem(
        mbl_no='ZIMUSNH1160339',
        vessel='CAPE TAINARO',
        voyage='3',
        por=LocationItem(name=None),
        pol=LocationItem(name="SHANGHAI (SH), CHINA. PEOPLE'S REPUBLIC"),
        pod=LocationItem(name='SAVANNAH (GA), U.S.A.'),
        final_dest=LocationItem(un_lo_code='USNVL', name=None),
        etd='17-Oct-2019',
        eta='13-Nov-2019',
        deliv_eta='19-Nov-2019',
    )

    assert results[2] == ContainerItem(
        container_key='GAOU6099859',
        container_no='GAOU6099859',
    )

    assert results[3] == ContainerStatusItem(
        container_key='GAOU6099859',
        description='Vessel departure from Port of Loading to Port of Discharge',
        local_date_time='17-Oct-2019 21:31',
        location=LocationItem(name="SHANGHAI (SH), CHINA. PEOPLE'S REPUBLIC"),
    )

    assert results[7] == ContainerItem(
        container_key='TCNU2750709',
        container_no='TCNU2750709',
    )
