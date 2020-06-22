from typing import List

from crawler.core_carrier.request_helpers import RequestOption


def verify(results: List):
    assert isinstance(results[0], RequestOption)
    assert results[0].url == (
        f'http://moc.oocl.com/party/cargotracking/ct_search_from_other_domain.jsf;'
        f'jsessionid=n8XBQ52UdPTKMYF_v9Y847OP0R9jTvdgdpOa-_ySJ-0AssuZ6yAf!1368327407?'
        f'ANONYMOUS_TOKEN=AhKikJsQRehJvNqtZpUjMCCOOCL&ENTRY=MCC&ENTRY_TYPE=OOCL&PREFER_LANGUAGE=en-US'
    )
    assert results[0].form_data == {
        'hiddenForm:searchType': 'BL',
        'hiddenForm:billOfLadingNumber': '2634031060',
        'hiddenForm:containerNumber': '',
        'hiddenForm_SUBMIT': '1',
        'hiddenForm:_link_hidden_': 'hiddenForm:goToCargoTrackingBL',
        'jsf_tree_64': (
            '1HdYiTH+P6aCi+7r36bgDBmkCLMZA0motGw7omBDXW8ifDoFRmtL2tZ8gkvZjz4VxXiR+IeF1KXrZq9G0/aFjQ4YQ2pcHx4X/OfYgS0PXH'
            'PzYsTwanH8Hz5ZWtEZszvNPHR5j6GxQw9dytLI3FhMFcO+J7MPPIxUsDE3or9Pr5v4N3QkX6thQLJd65vyupBKNg0DHGO0EgPMvfwQFF1j'
            '0hAfqNgeQMfd03yaDw01ZPcrw2HBtlW/gT5wahDbvlssEip5LA+pQb3zkeEvs+xDOKIx6e/UT6QKAmXG1XU/x3J29bk4G+nZhsqS0flFBg'
            'ZlZmV9tlRkYKxiMxczmJN1sKE4TdxGg6abXtlug4iJsF8Z06Owl9q7OK3hu44BAa+rUBKzhyQFTK66KIU6TjsxP+1eMOMUD4mE5uGOjqMD'
            '7Z35caQZJnIUDdoGs1T58tPIyxiIhJJn1G5q+9Emaw3jeDmsVDd4qH6Th5SDc2iW2ULZ7NVu6GU4dKR/nbgU1QdRtckqnoXzBf5FDPKYb6'
            '5aU61DxoTR2ykqskVGoz9+eihj+uAFWVUc35b/dCBxOhIRInmrxvAUEN6m34ZJSpGqf0KHWF7kXE+l4nfxJCP7dxc+xNx44C4ySw=='
        ),
        'jsf_state_64': (
            '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'
            'GabyzF7z47H71EM='
        ),
        'jsf_viewid': '/cargotracking/ct_search_from_other_domain.jsp',
    }


