from crawler.core_carrier.items import ContainerItem
from crawler.core_carrier.request_helpers import RequestOption


def verify(results, mbl_no):
    expect_url_fmt = (
        'http://elines.coscoshipping.com/ebtracking/public/container/status/{container_no}'
        '?billNumber={mbl_no}&timestamp='
    )

    assert results[0] == ContainerItem(
        container_key='UETU517168',
        container_no='UETU5171688',
    )

    expect_url0 = expect_url_fmt.format(container_no='UETU5171688', mbl_no=mbl_no)
    assert isinstance(results[1], RequestOption)
    assert results[1].url.startswith(expect_url0)

    assert results[2] == ContainerItem(
        container_key='TEMU696641',
        container_no='TEMU6966419',
    )

    expect_url1 = expect_url_fmt.format(container_no='TEMU6966419', mbl_no=mbl_no)
    assert isinstance(results[3], RequestOption)
    assert results[3].url.startswith(expect_url1)
