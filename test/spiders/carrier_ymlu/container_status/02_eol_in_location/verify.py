from crawler.core_carrier.items import ContainerStatusItem, LocationItem


def verify(results):
    assert results[1] == ContainerStatusItem(
        container_key='DRYU4228115',
        description='Empty to Shipper',
        local_date_time='2019/10/20 19:08',
        location=LocationItem(name='NINGBO (CMICTChina Merchants International Container Terminal in Daxie Island)'),
        transport=None,
    )
