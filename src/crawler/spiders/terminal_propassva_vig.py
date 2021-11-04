from crawler.core_terminal.propassva_share_spider import PropassvaShareSpider


class TerminalPropassvaVigSpider(PropassvaShareSpider):
    firms_code = "N195"
    name = "terminal_propassva_vig"
