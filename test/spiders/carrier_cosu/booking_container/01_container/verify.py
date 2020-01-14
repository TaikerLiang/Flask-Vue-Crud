from crawler.core_carrier.items import ContainerItem
from crawler.core_carrier.rules import RoutingRequest


def verify(results, booking_no):
    expect_url_fmt = (
        'http://elines.coscoshipping.com/ebtracking/public/container/status/{container_no}'
        '?bookingNumber={booking_no}&timestamp='
    )

    assert results[0] == ContainerItem(
        container_key='TEMU632927',
        container_no='TEMU6329278',
    )

    expect_url = expect_url_fmt.format(container_no='TEMU6329278', booking_no=booking_no)
    assert isinstance(results[1], RoutingRequest)
    assert results[1].request.url.startswith(expect_url)
