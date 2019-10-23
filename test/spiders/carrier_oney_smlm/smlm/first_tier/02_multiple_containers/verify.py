from scrapy import Request

from crawler.core_carrier.items import MblItem, ContainerItem
from crawler.spiders.carrier_oney_smlm import VesselRoutingRule, ReleaseStatusRoutingRule, ContainerStatusRoutingRule, \
    RailInfoRoutingRule
from test.spiders.utils import convert_formdata_to_bytes


def verify(results):
    assert results[0] == MblItem(mbl_no='SHFA9A128100')

    assert isinstance(results[1], Request)
    assert results[1].url == 'https://esvc.smlines.com/smline/CUP_HOM_3301GS.do'
    formdata = {
        'f_cmd': VesselRoutingRule.f_cmd,
        'bkg_no': 'SHFA9A128100',
    }
    assert results[1].body == convert_formdata_to_bytes(formdata)

    assert results[2] == ContainerItem(
        container_key='FCIU2480151',
        container_no='FCIU2480151',
    )

    assert isinstance(results[3], Request)
    formdata = {
        'f_cmd': ContainerStatusRoutingRule.f_cmd,
        'cntr_no': 'FCIU2480151',
        'bkg_no': 'SHFA9A128100',
        'cop_no': 'CSHA9918403939',
    }
    assert results[3].body == convert_formdata_to_bytes(formdata)

    assert isinstance(results[4], Request)
    formdata = {
        'f_cmd': ReleaseStatusRoutingRule.f_cmd,
        'cntr_no': 'FCIU2480151',
        'bkg_no': 'SHFA9A128100',
    }
    assert results[4].body == convert_formdata_to_bytes(formdata)

    assert isinstance(results[5], Request)
    formdata = {
        'f_cmd': RailInfoRoutingRule.f_cmd,
        'cop_no': 'CSHA9918403939',
    }
    assert results[5].body == convert_formdata_to_bytes(formdata)

    assert results[14] == ContainerItem(
        container_key='CAIU6468881',
        container_no='CAIU6468881',
    )

    assert isinstance(results[15], Request)
    formdata = {
        'f_cmd': ContainerStatusRoutingRule.f_cmd,
        'cntr_no': 'CAIU6468881',
        'bkg_no': 'SHFA9A128100',
        'cop_no': 'CSHA9918403940',
    }
    assert results[15].body == convert_formdata_to_bytes(formdata)

    assert isinstance(results[16], Request)
    formdata = {
        'f_cmd': ReleaseStatusRoutingRule.f_cmd,
        'cntr_no': 'CAIU6468881',
        'bkg_no': 'SHFA9A128100',
    }
    assert results[16].body == convert_formdata_to_bytes(formdata)

    assert isinstance(results[17], Request)
    formdata = {
        'f_cmd': RailInfoRoutingRule.f_cmd,
        'cop_no': 'CSHA9918403940',
    }
    assert results[17].body == convert_formdata_to_bytes(formdata)

