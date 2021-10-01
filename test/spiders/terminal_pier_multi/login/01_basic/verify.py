from crawler.core_terminal.request_helpers import RequestOption

def verify(results):
    assert isinstance(results[0], RequestOption)
    assert results[0].rule_name == 'SEARCH_CONTAINER'
    assert results[0].form_data['searchBy'] == 'CTR'
    assert results[0].form_data['numbers'] == 'DFSU7596831'
