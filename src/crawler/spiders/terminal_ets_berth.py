from crawler.core_terminal.ets_share_spider import EtsShareSpider, CompanyInfo


class TerminalEtsBerthSpider(EtsShareSpider):
    firms_code = "Y124"
    name = "terminal_ets_berth"
    company_info = CompanyInfo(
        email="w87818@yahoo.com.tw",
        password="Bb1234567890",
    )
