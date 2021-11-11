from crawler.core_carrier.items import ContainerItem, ContainerStatusItem, LocationItem


def verify(results):
    assert results[0] == ContainerItem(
        container_key="ACLU9685173",
        container_no="ACLU9685173",
    )

    assert results[1] == ContainerStatusItem(
        container_key="ACLU9685173",
        description="Received empty at",
        location=LocationItem(name="Port Newark, Nj-B51 (Pnct),New Jersey,U.S.A. 07114"),
        local_date_time="11/09/21 16:25",
        vessel=None,
    )

    assert results[2] == ContainerStatusItem(
        container_key="ACLU9685173",
        description="Departed from",
        location=LocationItem(name="Port Newark, Nj-B51 (Pnct),New Jersey,U.S.A. 07114"),
        local_date_time="11/04/21 16:58",
        vessel="ATLANTIC SKY/ATK7621",
    )

    assert results[3] == ContainerStatusItem(
        container_key="ACLU9685173",
        description="Discharged from vessel ATLANTIC SKY/ATK7621",
        location=LocationItem(name="Port Newark, Nj-B51 (Pnct),New Jersey,U.S.A. 07114"),
        local_date_time="11/01/21 15:10",
        vessel="ATLANTIC SKY/ATK7621",
    )

    assert results[4] == ContainerStatusItem(
        container_key="ACLU9685173",
        description="The ETA at the port of Discharge",
        location=LocationItem(name="Port Newark, Nj-B51 (Pnct),New Jersey,U.S.A. 07114"),
        local_date_time="11/01/21 07:48",
        vessel="ATLANTIC SKY/ATK7621",
    )

    assert results[6] == ContainerStatusItem(
        container_key="ACLU9685173",
        description="Loaded full on vessel ATLANTIC SKY/ATK7621",
        location=LocationItem(name=None),
        local_date_time="10/22/21 04:17",
        vessel="ATLANTIC SKY/ATK7621",
    )

    assert results[7] == ContainerStatusItem(
        container_key="ACLU9685173",
        description="Received for vessel ATLANTIC SKY/ATK7621",
        location=LocationItem(name="Liverpool Seaforth,United Kingdom L21.1"),
        local_date_time="10/13/21 13:42",
        vessel="ATLANTIC SKY/ATK7621",
    )
