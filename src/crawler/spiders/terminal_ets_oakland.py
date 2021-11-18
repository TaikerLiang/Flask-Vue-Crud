from crawler.core_terminal.ets_share_spider import EtsShareSpider, CompanyInfo


class TerminalEtsOaklandSpider(EtsShareSpider):
    firms_code = "WBA5"
    name = "terminal_ets_oakland"
    company_info = CompanyInfo(
        email="w87818@yahoo.com.tw",
        password="Bb1234567890",
    )
