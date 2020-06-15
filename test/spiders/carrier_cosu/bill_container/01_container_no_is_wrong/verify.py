from crawler.core_carrier.items import ContainerItem
from crawler.core_carrier.request_helpers import RequestOption


def verify(results, mbl_no):
    expect_url_fmt = (
        'http://elines.coscoshipping.com/ebtracking/public/container/status/{container_no}'
        '?billNumber={mbl_no}&timestamp='
    )

    assert results[0] == ContainerItem(
        container_key='OOLU364716',
        container_no='OOLU3647169',
    )

    expect_url = expect_url_fmt.format(container_no='OOLU3647169', mbl_no=mbl_no)
    assert isinstance(results[1], RequestOption)
    assert results[1].url.startswith(expect_url)
