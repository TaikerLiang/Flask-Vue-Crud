from crawler.core_terminal.ets_share_spider import EtsShareSpider, CompanyInfo


class TerminalEtsBenENutterSpider(EtsShareSpider):
    firms_code = "Y738"
    name = "terminal_ets_ben_e_nutter"
    company_info = CompanyInfo(
        email="w87818@yahoo.com.tw",
        password="Bb1234567890",
    )
