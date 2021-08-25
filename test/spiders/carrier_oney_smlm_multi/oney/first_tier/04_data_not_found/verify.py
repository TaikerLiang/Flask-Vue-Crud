from crawler.core_carrier.items import MblItem, ContainerItem, ExportErrorData
from crawler.core_carrier.request_helpers import RequestOption
from crawler.core_carrier.oney_smlm_multi_share_spider import (
    VesselRoutingRule,
    ReleaseStatusRoutingRule,
    ContainerStatusRoutingRule,
    RailInfoRoutingRule,
)
from crawler.core_carrier.exceptions import CARRIER_RESULT_STATUS_ERROR


def verify(results):
    assert results[0] == MblItem(mbl_no='RICBDW223900', task_id=1)

    assert isinstance(results[1], RequestOption)
    assert results[1].rule_name == VesselRoutingRule.name
    assert results[1].form_data == {
        'f_cmd': VesselRoutingRule.f_cmd,
        'bkg_no': 'RICBDW223900',
    }

    assert results[2] == MblItem(mbl_no='RICBDK658400', task_id=2)

    assert isinstance(results[3], RequestOption)
    assert results[3].rule_name == VesselRoutingRule.name
    assert results[3].form_data == {
        'f_cmd': VesselRoutingRule.f_cmd,
        'bkg_no': 'RICBDK658400',
    }

    assert results[4] == ExportErrorData(
        mbl_no='DALA35925000',
        status=CARRIER_RESULT_STATUS_ERROR,
        detail='Data was not found',
        task_id=3,
    )

    assert results[5] == ContainerItem(
        container_key='NYKU3438324',
        container_no='NYKU3438324',
        task_id=2,
    )

    assert isinstance(results[6], RequestOption)
    assert results[6].rule_name == ContainerStatusRoutingRule.name
    assert results[6].form_data == {
        'f_cmd': ContainerStatusRoutingRule.f_cmd,
        'cntr_no': 'NYKU3438324',
        'bkg_no': 'RICBDK658400',
        'cop_no': 'CRIC1603067489',
    }

    assert isinstance(results[7], RequestOption)
    assert results[7].rule_name == ReleaseStatusRoutingRule.name
    assert results[7].form_data == {
        'f_cmd': ReleaseStatusRoutingRule.f_cmd,
        'cntr_no': 'NYKU3438324',
        'bkg_no': 'RICBDK658400',
    }

    assert isinstance(results[8], RequestOption)
    assert results[8].rule_name == RailInfoRoutingRule.name
    assert results[8].form_data == {
        'f_cmd': RailInfoRoutingRule.f_cmd,
        'cop_no': 'CRIC1603067489',
    }

    assert results[37] == ContainerItem(
        container_key='TCLU3191927',
        container_no='TCLU3191927',
        task_id=1,
    )

    assert isinstance(results[38], RequestOption)
    assert results[38].rule_name == ContainerStatusRoutingRule.name
    assert results[38].form_data == {
        'f_cmd': ContainerStatusRoutingRule.f_cmd,
        'cntr_no': 'TCLU3191927',
        'bkg_no': 'RICBDW223900',
        'cop_no': 'CRIC1608275197',
    }

    assert isinstance(results[39], RequestOption)
    assert results[39].rule_name == ReleaseStatusRoutingRule.name
    assert results[39].form_data == {
        'f_cmd': ReleaseStatusRoutingRule.f_cmd,
        'cntr_no': 'TCLU3191927',
        'bkg_no': 'RICBDW223900',
    }

    assert isinstance(results[40], RequestOption)
    assert results[40].rule_name == RailInfoRoutingRule.name
    assert results[40].form_data == {
        'f_cmd': RailInfoRoutingRule.f_cmd,
        'cop_no': 'CRIC1608275197',
    }
