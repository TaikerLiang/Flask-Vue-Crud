from crawler.core_carrier.items import MblItem, ContainerItem


def verify(results):
    assert results[0] == MblItem(
        freight_date=None,
        us_customs_date=None,
        us_filing_date=None,
        firms_code=None,
    )

    assert results[1] == ContainerItem(
        container_key='TCLU7088049',
        last_free_day=None,
    )
