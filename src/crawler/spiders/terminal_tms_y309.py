from crawler.core_terminal.tms_share_spider import CompanyInfo, TmsSharedSpider


class TerminalPctSpider(TmsSharedSpider):
    firms_code = "Y309"
    name = "terminal_tms_long_beach_multi"
    terminal_id = 1
    company_info = CompanyInfo(
        email="Hardcore",
        password="Goft@220222",
    )
