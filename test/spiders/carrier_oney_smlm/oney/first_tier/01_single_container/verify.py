from scrapy import Request

from crawler.core_carrier.items import MblItem, ContainerItem
from crawler.spiders.carrier_oney_smlm import ReleaseStatusRoutingRule, ContainerStatusRoutingRule, \
    RailInfoRoutingRule, VesselRoutingRule
from test.spiders.utils import convert_formdata_to_bytes


def verify(results):
    assert results[0] == MblItem(mbl_no='SH9FSK690300')

    assert isinstance(results[1], Request)
    assert results[1].url == 'https://ecomm.one-line.com/ecom/CUP_HOM_3301GS.do'
    formdata = {
        'f_cmd': VesselRoutingRule.f_cmd,
        'bkg_no': 'SH9FSK690300',
    }
    assert results[1].body == convert_formdata_to_bytes(formdata)

    assert results[2] == ContainerItem(
        container_key='CLHU9129958',
        container_no='CLHU9129958',
    )

    assert isinstance(results[3], Request)
    formdata = {
        'f_cmd': ContainerStatusRoutingRule.f_cmd,
        'cntr_no': 'CLHU9129958',
        'bkg_no': 'SH9FSK690300',
        'cop_no': 'CSHA9925486010',
    }
    assert results[3].body == convert_formdata_to_bytes(formdata)

    assert isinstance(results[4], Request)
    formdata = {
        'f_cmd': ReleaseStatusRoutingRule.f_cmd,
        'cntr_no': 'CLHU9129958',
        'bkg_no': 'SH9FSK690300',
    }
    assert results[4].body == convert_formdata_to_bytes(formdata)

    assert isinstance(results[5], Request)
    formdata = {
        'f_cmd': RailInfoRoutingRule.f_cmd,
        'cop_no': 'CSHA9925486010',
    }
    assert results[5].body == convert_formdata_to_bytes(formdata)


