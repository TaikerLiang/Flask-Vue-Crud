from crawler.core_carrier.items import MblItem, ContainerItem
from crawler.core_carrier.rules import RoutingRequest
from crawler.spiders.carrier_oney_smlm import ReleaseStatusRoutingRule, ContainerStatusRoutingRule, \
    RailInfoRoutingRule, VesselRoutingRule
from test.spiders.utils import convert_formdata_to_bytes


def verify(results):
    assert results[0] == MblItem(
        mbl_no='SHSM9C747300',
    )

    assert isinstance(results[1], RoutingRequest)
    assert results[1].request.url == 'https://esvc.smlines.com/smline/CUP_HOM_3301GS.do'
    formdata = {
        'f_cmd': VesselRoutingRule.f_cmd,
        'bkg_no': 'SHSM9C747300',
    }
    assert results[1].request.body == convert_formdata_to_bytes(formdata)

    assert results[2] == ContainerItem(
        container_key='CCLU3451951',
        container_no='CCLU3451951',
    )

    assert isinstance(results[3], RoutingRequest)
    formdata = {
        'f_cmd': ContainerStatusRoutingRule.f_cmd,
        'cntr_no': 'CCLU3451951',
        'bkg_no': 'SHSM9C747300',
        'cop_no': 'CSHA9827358813',
    }
    assert results[3].request.body == convert_formdata_to_bytes(formdata)

    assert isinstance(results[4], RoutingRequest)
    formdata = {
        'f_cmd': ReleaseStatusRoutingRule.f_cmd,
        'cntr_no': 'CCLU3451951',
        'bkg_no': 'SHSM9C747300',
    }
    assert results[4].request.body == convert_formdata_to_bytes(formdata)

    assert isinstance(results[5], RoutingRequest)
    formdata = {
        'f_cmd': RailInfoRoutingRule.f_cmd,
        'cop_no': 'CSHA9827358813',
    }
    assert results[5].request.body == convert_formdata_to_bytes(formdata)




