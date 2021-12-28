from crawler.core_carrier.items import MblItem, ContainerItem


def verify(results):
    assert results[0] == MblItem(
        freight_date='2019-09-03 22:46',
        us_customs_date='2019-09-27 03:01',
        us_filing_date=None,
        firms_code='H903',
        task_id=1,
    )

    assert results[1] == ContainerItem(
        container_key='CCLU3451951',
        last_free_day='2019-09-29 00:00',
        terminal=None,
        task_id=1,
    )
