from crawler.core_carrier.items_new import ContainerItem, MblItem


def verify(results):
    assert results[0] == MblItem(
        freight_date="2019-09-29 07:24",
        us_customs_date=None,
        us_filing_date="2019-09-27 06:57",
        firms_code="H099",
        task_id=1,
    )

    assert results[1] == ContainerItem(
        container_key="CLHU9129958",
        last_free_day=None,
        terminal={"name": "Y258"},
        task_id=1,
    )
