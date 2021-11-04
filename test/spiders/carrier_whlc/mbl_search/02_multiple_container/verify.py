from typing import List


def verify(results: List):
    assert results[0] == ({'container_no': 'WHLU2944422',
                           'detail_j_idt': 'j_idt39:0:ctnr_list_more_detail',
                           'history_j_idt': 'j_idt39:0:ctnr_list_more_history'
                           })
    assert results[1] == ({'container_no': 'WHSU2162814',
                           'detail_j_idt': 'j_idt39:1:ctnr_list_more_detail',
                           'history_j_idt': 'j_idt39:1:ctnr_list_more_history'
                           })
