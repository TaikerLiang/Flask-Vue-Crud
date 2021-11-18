from crawler.core_terminal.ets_share_spider import EtsShareSpider, CompanyInfo


class TerminalEtsOaklandSpider(EtsShareSpider):
    firms_code = "X215"
    name = "terminal_ets_oakland"
    company_info = CompanyInfo(
        email="w87818@yahoo.com.tw",
        password="Bb1234567890",
    )
