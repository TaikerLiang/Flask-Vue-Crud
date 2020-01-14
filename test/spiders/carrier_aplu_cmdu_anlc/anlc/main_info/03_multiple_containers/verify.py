from crawler.spiders.carrier_aplu_cmdu_anlc import ContainerStatusRoutingRule, CarrierAnlcSpider
from test.spiders.utils import extract_url_from


def verify(results):
    expect_url_fmt = \
        'https://www.anl.com.au/ebusiness/tracking/detail/{container_no}?SearchCriteria=BL&SearchByReference={mbl_no}'

    expect_url = expect_url_fmt.format(container_no='TEXU1028151', mbl_no='AWT0143454')

    assert results[0].request.url == expect_url

    expect_url = expect_url_fmt.format(container_no='AMCU2500184', mbl_no='AWT0143454')

    assert results[1].request.url == expect_url

    expect_url = expect_url_fmt.format(container_no='TLLU1233702', mbl_no='AWT0143454')

    assert results[2].request.url == expect_url

    expect_url = expect_url_fmt.format(container_no='TCLU7717882', mbl_no='AWT0143454')

    assert results[3].request.url == expect_url
