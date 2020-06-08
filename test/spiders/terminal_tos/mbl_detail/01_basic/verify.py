from crawler.core_terminal.items import TerminalItem


def verify(results):
    assert results[0] == TerminalItem(
        vessel='YM MUTUALITY',
        voyage='075E',
    )
