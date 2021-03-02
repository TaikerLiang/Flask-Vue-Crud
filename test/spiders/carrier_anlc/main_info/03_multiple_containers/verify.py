def verify(results):
    expect_url_fmt = \
        'https://www.anl.com.au/ebusiness/tracking/detail/{container_no}?SearchCriteria=BL&SearchByReference={mbl_no}'

    expect_url = expect_url_fmt.format(container_no='TEXU1028151', mbl_no='AWT0143454')

    assert results[0].url == expect_url

    expect_url = expect_url_fmt.format(container_no='AMCU2500184', mbl_no='AWT0143454')

    assert results[1].url == expect_url

    expect_url = expect_url_fmt.format(container_no='TLLU1233702', mbl_no='AWT0143454')

    assert results[2].url == expect_url

    expect_url = expect_url_fmt.format(container_no='TCLU7717882', mbl_no='AWT0143454')

    assert results[3].url == expect_url
