from typing import List

from crawler.core_carrier.request_helpers import RequestOption


def verify(results: List):
    assert isinstance(results[0], RequestOption)
    assert results[0].form_data['hiddenForm:token'] == ''
    assert results[0].form_data['jsf_tree_64'] == (
        '1HdYiTH+P6YThvE4ydXzBPTk9wPMt1T/5w14XhMu2/El0b+CrH98Db8uq5j+eUAQZaiQTMDYDbq3Tf/iiwiO9G5TidRB7FROOoEWREzpXvuL/H'
        'QQeHyOXDq3WG6sFvMKD2+upaA5yYuAyjpI593Jew+3TSBOXoewxVvXqy1KuWu+SOImBe+1QXYLj918Kz3xMstsnuZcre8D8iOqhu6cZFWnRb4V'
        '1jLtMO8sFfzIiWy0vc5NwzUMddgDcg7Qn+m9Ha5WVfA+G+szxlEpLW8Ko9evAdTx9bXzmfVCXcRFLG/t5rrI1vqhd1W207XY69yhW4qhECEQaY'
        '5B4UaybPaFGqm+fHEzvt9MZJN9W3v0Ecw792oQvBdFS+9UdtPED/SC3Qb3Saxxpoag7oppyDF19rCTK9HoMmC1kGCvzCRDwKoHw734iKuXP3po'
        '1RbcvIKXUG6IOM1dhShwUTOABgU1sKg3K42ljYoS+HSHA6kEpfYx/KExRyB2VLuzjaagw45PPpO3nRyrqtdDNrMof0k54hUucSZqHibuCQLMhS'
        'pxv2degtSnBhEdJt8/n/pn6tHNtZ2lY2KjGHch7dn9OEqq8ujJs+CBw2qaEvtM0YAumXFM+GV1KXOYmb+dr+5U8i3v6+wsX/0jdIA='
    )
    assert results[0].form_data['jsf_state_64'] == (
        '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'
    )
    assert results[0].form_data['USER_TOKEN'] == 'wOwwhWrcsRIFeMXfinjYMCCOOCL'


