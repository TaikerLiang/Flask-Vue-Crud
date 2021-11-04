from crawler.core_terminal.ets_share_spider import EtsShareSpider, CompanyInfo


class TerminalPierceCountySpider(EtsShareSpider):
    firms_code = "X215"
    name = "terminal_ets_pierce_county"
    company_info = CompanyInfo(
        email="w87818@yahoo.com.tw",
        password="Bb1234567890",
    )
