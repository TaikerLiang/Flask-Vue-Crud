from crawler.core_carrier.items import MblItem, ContainerItem, ContainerStatusItem, LocationItem


def verify(results):
    assert results[0] == MblItem(
        mbl_no='969881899',
        por=LocationItem(name='Kaohsiung Hanjin Terminal Pier76-78 -- Kaohsiung (TW)'),
        final_dest=LocationItem(name=None),
    )

    assert results[1] == ContainerItem(
        container_key='MRKU0324235', container_no='MRKU0324235', final_dest_eta='2020-01-07T08:00:00.000'
    )

    assert results[2] == ContainerItem(
        container_key='MRKU0689887', container_no='MRKU0689887', final_dest_eta='2020-01-07T08:00:00.000'
    )

    assert results[8] == ContainerItem(
        container_key='PONU1795714', container_no='PONU1795714', final_dest_eta='2020-01-07T08:00:00.000'
    )
