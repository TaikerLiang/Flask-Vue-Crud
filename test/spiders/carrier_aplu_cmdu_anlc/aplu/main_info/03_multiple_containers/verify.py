from crawler.spiders.carrier_aplu_cmdu_anlc import CarrierApluSpider, ContainerStatusRoutingRule
from test.spiders.utils import extract_url_from


def verify(results):
    expect_url_fmt = \
        'http://www.apl.com/ebusiness/tracking/detail/{container_no}?SearchCriteria=BL&SearchByReference={mbl_no}'

    expect_url = expect_url_fmt.format(container_no='TCNU1868370', mbl_no='SHSE015942')

    assert results[0].request.url == expect_url

    expect_url = expect_url_fmt.format(container_no='APHU6968583', mbl_no='SHSE015942')

    assert results[1].request.url == expect_url
