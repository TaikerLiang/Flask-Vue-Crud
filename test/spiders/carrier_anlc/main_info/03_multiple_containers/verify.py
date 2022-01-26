from typing import List


def verify(results: List):
    results.pop(0)

    expect_url_fmt = "https://www.anl.com.au/ebusiness/tracking/detail/{container_no}?SearchCriteria=Booking&SearchByReference={mbl_no}"

    expect_url = expect_url_fmt.format(container_no='TEXU1028151', mbl_no='AWT0143454')

    assert results[0].url == expect_url

    expect_url = expect_url_fmt.format(container_no='AMCU2500184', mbl_no='AWT0143454')

    assert results[1].url == expect_url

    expect_url = expect_url_fmt.format(container_no='TLLU1233702', mbl_no='AWT0143454')

    assert results[2].url == expect_url

    expect_url = expect_url_fmt.format(container_no='TCLU7717882', mbl_no='AWT0143454')

    assert results[3].url == expect_url


def multi_verify(results: List):
    results.pop(0)

    expect_url_fmt = "https://www.anl.com.au/ebusiness/tracking/detail/{container_no}?SearchCriteria=Booking&SearchByReference={mbl_no}"

    expect_url = expect_url_fmt.format(container_no='TEXU1028151', mbl_no='AWT0143454')

    assert results[0].url == expect_url

    expect_url = expect_url_fmt.format(container_no='AMCU2500184', mbl_no='AWT0143454')

    assert results[1].url == expect_url

    expect_url = expect_url_fmt.format(container_no='TLLU1233702', mbl_no='AWT0143454')

    assert results[2].url == expect_url

    expect_url = expect_url_fmt.format(container_no='TCLU7717882', mbl_no='AWT0143454')

    assert results[3].url == expect_url
