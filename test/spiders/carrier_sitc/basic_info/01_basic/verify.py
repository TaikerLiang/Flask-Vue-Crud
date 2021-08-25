import scrapy

from crawler.core_carrier.items import MblItem, LocationItem, VesselItem, ContainerItem
from crawler.core_carrier.request_helpers import RequestOption
from crawler.spiders.carrier_sitc import ContainerStatusRoutingRule


def verify(results):
    assert results[0] == MblItem(
        mbl_no='SITDSHSGZ02389',
        pol=LocationItem(name='上海'),
        final_dest=LocationItem(name='胡志明'),
    )
    assert results[1] == VesselItem(
        ata='2021-07-24 11:00',
        atd='2021-07-19 06:13',
        eta='2021-07-15 20:00:00',
        etd='2021-07-09 23:00:00',
        pod=LocationItem(name='HO CHI MINH'),
        pol=LocationItem(name='SHANGHAI'),
        vessel='SITC JAKARTA',
        vessel_key='SITC JAKARTA',
        voyage='2114'
    )
    assert results[2] == ContainerItem(
        container_key='TEXU1590148',
        container_no='TEXU1590148',
    )
    assert isinstance(results[3], RequestOption)
    assert results[3].url == 'http://api.sitcline.com/doc/cargoTrack/detail?blNo=SITDSHSGZ02389&containerNo=TEXU1590148'
    assert results[3].rule_name == ContainerStatusRoutingRule.name

    assert results[8] == ContainerItem(
        container_key='SEGU7346329',
        container_no='SEGU7346329',
    )
    assert isinstance(results[9], RequestOption)
    assert results[9].url == 'http://api.sitcline.com/doc/cargoTrack/detail?blNo=SITDSHSGZ02389&containerNo=SEGU7346329'
    assert results[9].rule_name == ContainerStatusRoutingRule.name
