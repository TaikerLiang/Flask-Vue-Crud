from crawler.core_terminal.ets_share_spider import EtsShareSpider, CompanyInfo


class TerminalBerthSpider(EtsShareSpider):
    firms_code = "Y124"
    name = "terminal_berth_multi"
    company_info = CompanyInfo(
        email="w87818@yahoo.com.tw",
        password="Bb1234567890",
    )
