from typing import List


def verify(results: List):
    extract_hold = lambda content: [ele.strip() for ele in content.split("\\")]

    assert results[0][0] == "FCIU9155148"
    assert results[0][8] == "AVAILABLE FOR PICKUP"
    assert extract_hold(results[0][9]) == [""]
    assert results[0][2] == "RDO FORTUNE / 003W"

    assert results[1][0] == "FSCU8053140"
    assert results[1][8] == "\xa0"
    assert extract_hold(results[1][9]) == [""]
    assert results[1][2] == "CMA CGM BRAZIL / 005S"

    assert results[2][0] == "HDMU4748456"
    assert results[2][8] == "UNAVAILABLE"
    assert extract_hold(results[2][9]) == ["ENTRY REQ", "NO EIR"]
    assert results[2][2] == "MEISHAN BRIDGE / 0015E"

    assert results[3][0] == "TCNU7907787"
    assert results[3][8] == "AVAILABLE FOR PICKUP"
    assert extract_hold(results[3][9]) == [""]
    assert results[3][2] == "MSC NAOMI / 137A"
