from crawler.core_carrier.items import ContainerItem


def verify(results):
    assert results[0] == ContainerItem(**{
        'container_key': '1',
        'container_no': 'OOLU3647169',
    })

    expect_url = 'http://elines.coscoshipping.com/ebtracking/public/container/status/OOLU3647169?billNumber=6205749080&timestamp='
    assert results[1].url.startswith(expect_url)
