from crawler.core_carrier.items import MblItem, ContainerItem
from crawler.core_carrier.rules import RoutingRequest
from crawler.spiders.carrier_oney_smlm import VesselRoutingRule, ReleaseStatusRoutingRule, ContainerStatusRoutingRule, \
    RailInfoRoutingRule
from test.spiders.utils import convert_formdata_to_bytes


def verify(results):
    assert results[0] == MblItem(mbl_no='SHFA9A128100')

    assert isinstance(results[1], RoutingRequest)
    assert results[1].request.url == 'https://esvc.smlines.com/smline/CUP_HOM_3301GS.do'
    formdata = {
        'f_cmd': VesselRoutingRule.f_cmd,
        'bkg_no': 'SHFA9A128100',
    }
    assert results[1].request.body == convert_formdata_to_bytes(formdata)

    assert results[2] == ContainerItem(
        container_key='FCIU2480151',
        container_no='FCIU2480151',
    )

    assert isinstance(results[3], RoutingRequest)
    formdata = {
        'f_cmd': ContainerStatusRoutingRule.f_cmd,
        'cntr_no': 'FCIU2480151',
        'bkg_no': 'SHFA9A128100',
        'cop_no': 'CSHA9918403939',
    }
    assert results[3].request.body == convert_formdata_to_bytes(formdata)

    assert isinstance(results[4], RoutingRequest)
    formdata = {
        'f_cmd': ReleaseStatusRoutingRule.f_cmd,
        'cntr_no': 'FCIU2480151',
        'bkg_no': 'SHFA9A128100',
    }
    assert results[4].request.body == convert_formdata_to_bytes(formdata)

    assert isinstance(results[5], RoutingRequest)
    formdata = {
        'f_cmd': RailInfoRoutingRule.f_cmd,
        'cop_no': 'CSHA9918403939',
    }
    assert results[5].request.body == convert_formdata_to_bytes(formdata)

    assert results[14] == ContainerItem(
        container_key='CAIU6468881',
        container_no='CAIU6468881',
    )

    assert isinstance(results[15], RoutingRequest)
    formdata = {
        'f_cmd': ContainerStatusRoutingRule.f_cmd,
        'cntr_no': 'CAIU6468881',
        'bkg_no': 'SHFA9A128100',
        'cop_no': 'CSHA9918403940',
    }
    assert results[15].request.body == convert_formdata_to_bytes(formdata)

    assert isinstance(results[16], RoutingRequest)
    formdata = {
        'f_cmd': ReleaseStatusRoutingRule.f_cmd,
        'cntr_no': 'CAIU6468881',
        'bkg_no': 'SHFA9A128100',
    }
    assert results[16].request.body == convert_formdata_to_bytes(formdata)

    assert isinstance(results[17], RoutingRequest)
    formdata = {
        'f_cmd': RailInfoRoutingRule.f_cmd,
        'cop_no': 'CSHA9918403940',
    }
    assert results[17].request.body == convert_formdata_to_bytes(formdata)

