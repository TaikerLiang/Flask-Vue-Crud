from crawler.core_terminal.rules import RequestOption


def verify(results):
    assert isinstance(results[0], RequestOption)
    assert results[0].headers.get("Authorization") == "TOKEN"
