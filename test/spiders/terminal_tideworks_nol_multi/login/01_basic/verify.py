from crawler.core_terminal.request_helpers import RequestOption


def verify(results):
    assert isinstance(results[0], RequestOption)
    assert results[0].rule_name == "SEARCH_CONTAINER"
    assert results[0].form_data["searchBy"] == "CTR"
    assert results[0].form_data["numbers"] == "TRHU2178921"
    assert results[0].form_data["_csrf"] == "6e2d987a-4565-4be6-a968-82213502fd40"
    assert results[0].cookies == {"BNI_JSESSIONID": "0000000000000000000000000cb012ac0000921f"}
