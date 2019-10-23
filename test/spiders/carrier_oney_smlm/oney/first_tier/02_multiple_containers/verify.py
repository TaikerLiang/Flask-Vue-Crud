from scrapy import Request

from crawler.core_carrier.items import MblItem, ContainerItem
from crawler.spiders.carrier_oney_smlm import VesselRoutingRule, ReleaseStatusRoutingRule, ContainerStatusRoutingRule, \
    RailInfoRoutingRule
from test.spiders.utils import convert_formdata_to_bytes


def verify(results):
    assert results[0] == MblItem(mbl_no='SZPVF2740514')

    assert isinstance(results[1], Request)
    assert results[1].url == 'https://ecomm.one-line.com/ecom/CUP_HOM_3301GS.do'
    formdata = {
        'f_cmd': VesselRoutingRule.f_cmd,
        'bkg_no': 'SZPVF2740514',
    }
    assert results[1].body == convert_formdata_to_bytes(formdata)

    assert results[2] == ContainerItem(
        container_key='UETU5848871',
        container_no='UETU5848871',
    )

    assert isinstance(results[3], Request)
    formdata = {
        'f_cmd': ContainerStatusRoutingRule.f_cmd,
        'cntr_no': 'UETU5848871',
        'bkg_no': 'SZPVF2740514',
        'cop_no': 'CSZP9916113071',
    }
    assert results[3].body == convert_formdata_to_bytes(formdata)

    assert isinstance(results[4], Request)
    formdata = {
        'f_cmd': ReleaseStatusRoutingRule.f_cmd,
        'cntr_no': 'UETU5848871',
        'bkg_no': 'SZPVF2740514',
    }
    assert results[4].body == convert_formdata_to_bytes(formdata)

    assert isinstance(results[5], Request)
    formdata = {
        'f_cmd': RailInfoRoutingRule.f_cmd,
        'cop_no': 'CSZP9916113071',
    }
    assert results[5].body == convert_formdata_to_bytes(formdata)

    assert results[18] == ContainerItem(
        container_key='UETU5848906',
        container_no='UETU5848906',
    )

    assert isinstance(results[19], Request)
    formdata = {
        'f_cmd': ContainerStatusRoutingRule.f_cmd,
        'cntr_no': 'UETU5848906',
        'bkg_no': 'SZPVF2740514',
        'cop_no': 'CSZP9916113073',
    }
    assert results[19].body == convert_formdata_to_bytes(formdata)

    assert isinstance(results[20], Request)
    formdata = {
        'f_cmd': ReleaseStatusRoutingRule.f_cmd,
        'cntr_no': 'UETU5848906',
        'bkg_no': 'SZPVF2740514',
    }
    assert results[20].body == convert_formdata_to_bytes(formdata)

    assert isinstance(results[21], Request)
    formdata = {
        'f_cmd': RailInfoRoutingRule.f_cmd,
        'cop_no': 'CSZP9916113073',
    }
    assert results[21].body == convert_formdata_to_bytes(formdata)

