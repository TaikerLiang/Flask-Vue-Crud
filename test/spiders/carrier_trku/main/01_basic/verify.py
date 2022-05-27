from crawler.core_carrier.items import (
    ContainerItem,
    ContainerStatusItem,
    LocationItem,
    MblItem,
    VesselItem,
)


def verify(results):
    assert results[0] == MblItem(
        mbl_no="TRKU10023023",
        task_id="1",
        ata="May.13.2022",
        atd="Apr.22.2022",
    )
    assert results[1] == VesselItem(
        vessel="MELCHIOR SCHULTE",
        vessel_key="MELCHIOR SCHULTE",
        voyage="0US1BW1TK",
        atd="Apr.22.2022",
        etd=None,
        pol="EVYAPPORT",
        task_id="1",
    )
    assert results[2] == VesselItem(
        vessel="MELCHIOR SCHULTE",
        vessel_key="MELCHIOR SCHULTE",
        voyage="0US1BW1TK",
        ata=None,
        eta="May.13.2022",
        pod="Norfolk InternatIonal TermInal",
        task_id="1",
    )

    assert results[3] == ContainerItem(
        container_key="TRKU4428532",
        container_no="TRKU4428532",
        task_id="1",
    )

    assert results[4] == ContainerStatusItem(
        container_key="TRKU4428532",
        description="GATE OUT EMPTY",
        local_date_time="Apr.12.2022 00:00:01",
        location=LocationItem(name="EVYAPPORT"),
        vessel="MELCHIOR SCHULTE",
        task_id="1",
    )

    assert results[5] == ContainerStatusItem(
        container_key="TRKU4428532",
        description="GATE IN FULL",
        vessel="MELCHIOR SCHULTE",
        local_date_time="Apr.13.2022 00:00:01",
        location=LocationItem(name="EVYAPPORT"),
        task_id="1",
    )

    assert results[7] == ContainerStatusItem(
        container_key="TRKU4428532",
        description="FULL UNLOAD",
        vessel="MELCHIOR SCHULTE",
        local_date_time="May.13.2022",
        location=LocationItem(name="Norfolk InternatIonal TermInal"),
        task_id="1",
    )
