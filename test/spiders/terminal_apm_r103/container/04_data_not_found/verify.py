from crawler.core_terminal.items import InvalidContainerNoItem


def verify(results):
    assert results[0] == InvalidContainerNoItem(
        container_no='KOCU9871987',
    )