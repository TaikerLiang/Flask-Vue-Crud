from crawler.core_terminal.ets_share_spider import EtsShareSpider, CompanyInfo


class TerminalBenSpider(EtsShareSpider):
    firms_code = "Y738"
    name = "terminal_ets_ben"
    company_info = CompanyInfo(
        email="w87818@yahoo.com.tw",
        password="Bb1234567890",
    )
