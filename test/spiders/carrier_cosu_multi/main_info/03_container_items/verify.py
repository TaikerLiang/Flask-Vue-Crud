from crawler.core_carrier.items import ContainerItem


def verify(items):
    assert items[0] == ContainerItem(
        **{
            'task_id': '3',
            'container_key': 'CSNU639560',
            'container_no': 'CSNU6395607',
            'depot_last_free_day': None,
            'last_free_day': '2021-01-07 23:59:00.0',
        }
    )

    assert items[1] == ContainerItem(
        **{
            'task_id': '3',
            'container_key': 'CSNU695618',
            'container_no': 'CSNU6956185',
            'depot_last_free_day': None,
            'last_free_day': '2021-01-07 23:59:00.0',
        }
    )

    assert items[2] == ContainerItem(
        **{
            'task_id': '3',
            'container_key': 'CSNU710043',
            'container_no': 'CSNU7100439',
            'depot_last_free_day': None,
            'last_free_day': '2020-12-31 23:59:00.0',
        }
    )
