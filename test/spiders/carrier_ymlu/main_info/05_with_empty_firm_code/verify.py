from typing import List

from crawler.core_carrier.items import ContainerItem, LocationItem, MblItem
from crawler.core_carrier.request_helpers import RequestOption


def verify(results: List):
    assert results[0] == MblItem(
        mbl_no="I209431722",
        por=LocationItem(name="KAOHSIUNG (TWKHH)"),
        pol=LocationItem(name="KAOHSIUNG (TWKHH)"),
        pod=LocationItem(name="LAEM CHABANG (THLCB)"),
        place_of_deliv=LocationItem(name="LAEM CHABANG (THLCB)"),
        etd=None,
        atd="2022/02/26 02:15",
        eta=None,
        ata="2022/03/03 05:56",
        firms_code=None,
        carrier_status=None,
        carrier_release_date=None,
        customs_release_status=None,
        customs_release_date=None,
        berthing_time="2022/03/03 06:42",
        vessel="YM INSTRUCTION",
        voyage="283S (JTC207S)",
    )

    assert results[1] == ContainerItem(
        container_key="TGHU5296335",
        container_no="TGHU5296335",
        last_free_day=None,
        terminal_pod=LocationItem(name=None),
    )

    assert isinstance(results[2], RequestOption)
    assert results[2].url == (
        "https://www.yangming.com/e-service/Track_Trace/"
        "ctconnect.aspx?var=6kXS94MAUKku1eUXw6LbZEutRU6z%2b4lPhaStBOod9zUQmJ%2bP3qmLH%2fDDxTGM%2f%2bsE%2f78q1qU6BoFx425UlkDj%2bNtKivqMSG7%2f5%2bn1B3KxLjyP6AERrRqpyB9mfEF4d2mTp4RKozIF6bpCJmHTIARgiKR011Wl03iXTPK7EGt%2bVx8%3d"
    )

    assert results[3] == ContainerItem(
        container_key="YMLU5151195",
        container_no="YMLU5151195",
        last_free_day=None,
        terminal_pod=LocationItem(name=None),
    )

    assert isinstance(results[4], RequestOption)
    assert results[4].url == (
        "https://www.yangming.com/e-service/Track_Trace/"
        "ctconnect.aspx?var=6kXS94MAUKku1eUXw6LbZA8W19w55bM9J3EwU5raXyTFR8VF4s3AVYXhRHSnku4fYuyQ9oSpydX2J68L2dCLA%2fOTaED6TZsWWIIWLUSxQG0drQfW26n19iehUEueKJpPa%2feN5C0GIQlc%2b%2bFoSgGQOj%2fD71DD3GvwIIEEDHp0zBk%3d"
    )

    assert results[5] == ContainerItem(
        container_key="YMLU5179778",
        container_no="YMLU5179778",
        last_free_day=None,
        terminal_pod=LocationItem(name=None),
    )

    assert isinstance(results[6], RequestOption)
    assert results[6].url == (
        "https://www.yangming.com/e-service/Track_Trace/"
        "ctconnect.aspx?var=6kXS94MAUKku1eUXw6LbZA8W19w55bM9J3EwU5raXySENJWU9KfbPrXKb9RilsOP84MRS1hZUQQpYnnOQq%2fzh2RQB3cnipDqJcuVewUjTV6BxCs8sCl9OTkpnYNA0cfbHkJluy%2fIHod5tpqLT%2fZsCpXiq%2blxPZx6OIY8he2o6z0%3d"
    )
