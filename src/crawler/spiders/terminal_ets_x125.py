from crawler.core_terminal.ets_share_spider import EtsShareSpider, CompanyInfo


class TerminalEtsPierceCountySpider(EtsShareSpider):
    firms_code = "X215"
    name = "terminal_ets_pierce_county"
    company_info = CompanyInfo(
        email="w87818@yahoo.com.tw",
        password="Bb1234567890",
    )
