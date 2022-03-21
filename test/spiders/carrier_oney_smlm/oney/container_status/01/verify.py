from crawler.core_carrier.items_new import ContainerStatusItem, LocationItem


def verify(results):
    assert results[0] == ContainerStatusItem(
        container_key="CLHU9129958",
        description="Empty Container Release to Shipper",
        local_date_time="2019-09-28 10:44",
        location=LocationItem(name="SHANGHAI, SHANGHAI ,CHINA"),
        est_or_actual="A",
    )

    assert results[4] == ContainerStatusItem(
        container_key="CLHU9129958",
        description="'YM UNICORN 040E' Arrival at Port of Discharging",
        local_date_time="2019-10-18 14:00",
        location=LocationItem(name="LOS ANGELES, CA ,UNITED STATES"),
        est_or_actual="E",
    )

    assert results[14] == ContainerStatusItem(
        container_key="CLHU9129958",
        description="Empty Container Returned from Customer",
        local_date_time="2019-10-24 23:00",
        location=LocationItem(name="HENDERSON, CO ,UNITED STATES"),
        est_or_actual="E",
    )
