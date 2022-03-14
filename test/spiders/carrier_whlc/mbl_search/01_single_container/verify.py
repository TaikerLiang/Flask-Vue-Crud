from typing import List


def verify(results: List):
    assert results[0] == (
        {
            "container_no": "WHSU6570305",
            "detail_j_idt": "j_idt40:0:ctnr_list_more_detail",
            "history_j_idt": "j_idt40:0:ctnr_list_more_history",
        }
    )
