from typing import List


def verify(results: List):
    results.pop(0)

    expect_url_fmt = \
        'http://www.apl.com/ebusiness/tracking/detail/{container_no}?SearchCriteria=BL&SearchByReference={mbl_no}'

    expect_url = expect_url_fmt.format(container_no='ECMU9893257', mbl_no='NBSF301194')

    assert results[0].url == expect_url

    expect_url = expect_url_fmt.format(container_no='ECMU9836072', mbl_no='NBSF301194')

    assert results[1].url == expect_url
