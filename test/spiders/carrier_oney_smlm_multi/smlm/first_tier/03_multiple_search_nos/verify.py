from crawler.core_carrier.items import MblItem, ContainerItem, ExportErrorData
from crawler.core_carrier.request_helpers import RequestOption
from crawler.core_carrier.oney_smlm_share_spider import (
    VesselRoutingRule,
    ReleaseStatusRoutingRule,
    ContainerStatusRoutingRule,
    RailInfoRoutingRule,
)
from crawler.core_carrier.exceptions import CARRIER_RESULT_STATUS_ERROR


def verify(results):
    assert results[0] == ExportErrorData(
        mbl_no='SHSB1FY71701',
        status=CARRIER_RESULT_STATUS_ERROR,
        detail='Data was not found',
        task_id=1,
    )

    assert results[1] == MblItem(mbl_no='NJBH1A243500', task_id=2)

    assert isinstance(results[2], RequestOption)
    assert results[2].url == 'https://esvc.smlines.com/smline/CUP_HOM_3301GS.do'
    assert results[2].rule_name == VesselRoutingRule.name
    assert results[2].form_data == {
        'f_cmd': VesselRoutingRule.f_cmd,
        'bkg_no': 'NJBH1A243500',
    }

    assert results[3] == ContainerItem(
        container_key='DFSU2813575',
        container_no='DFSU2813575',
        task_id=2,
    )

    assert isinstance(results[4], RequestOption)
    assert results[4].rule_name == ContainerStatusRoutingRule.name
    assert results[4].form_data == {
        'f_cmd': ContainerStatusRoutingRule.f_cmd,
        'cntr_no': 'DFSU2813575',
        'bkg_no': 'NJBH1A243500',
        'cop_no': 'CNBO1517595958',
    }

    assert isinstance(results[5], RequestOption)
    assert results[5].rule_name == ReleaseStatusRoutingRule.name
    assert results[5].form_data == {
        'f_cmd': ReleaseStatusRoutingRule.f_cmd,
        'cntr_no': 'DFSU2813575',
        'bkg_no': 'NJBH1A243500',
    }

    assert isinstance(results[6], RequestOption)
    assert results[6].rule_name == RailInfoRoutingRule.name
    assert results[6].form_data == {
        'f_cmd': RailInfoRoutingRule.f_cmd,
        'cop_no': 'CNBO1517595958',
    }

    assert results[15] == ContainerItem(
        container_key='FCIU3915217',
        container_no='FCIU3915217',
        task_id=2,
    )

    assert isinstance(results[16], RequestOption)
    assert results[16].rule_name == ContainerStatusRoutingRule.name
    assert results[16].form_data == {
        'f_cmd': ContainerStatusRoutingRule.f_cmd,
        'cntr_no': 'FCIU3915217',
        'bkg_no': 'NJBH1A243500',
        'cop_no': 'CNBO1517595959',
    }

    assert isinstance(results[17], RequestOption)
    assert results[17].rule_name == ReleaseStatusRoutingRule.name
    assert results[17].form_data == {
        'f_cmd': ReleaseStatusRoutingRule.f_cmd,
        'cntr_no': 'FCIU3915217',
        'bkg_no': 'NJBH1A243500',
    }

    assert isinstance(results[18], RequestOption)
    assert results[18].rule_name == RailInfoRoutingRule.name
    assert results[18].form_data == {
        'f_cmd': RailInfoRoutingRule.f_cmd,
        'cop_no': 'CNBO1517595959',
    }
