from crawler.spiders.carrier_aplu_cmdu_anlc import ContainerStatusRoutingRule, CarrierCmduSpider
from test.spiders.utils import extract_url_from


def verify(results):
    expect_url_fmt = \
        'http://www.cma-cgm.com/ebusiness/tracking/detail/{container_no}?SearchCriteria=BL&SearchByReference={mbl_no}'

    expect_url = expect_url_fmt.format(container_no='ECMU9893257', mbl_no='NBSF301194')

    assert results[0].request.url == expect_url

    expect_url = expect_url_fmt.format(container_no='ECMU9836072', mbl_no='NBSF301194')

    assert results[1].request.url == expect_url
