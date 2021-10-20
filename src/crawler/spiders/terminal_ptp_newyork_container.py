from crawler.core_terminal.ptp_share_spider import PtpShareSpider


class TerminalNewYorkContainerSpider(PtpShareSpider):
    firms_code = "E005"
    name = "terminal_newyork_container"
