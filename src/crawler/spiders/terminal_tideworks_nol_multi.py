from crawler.core_terminal.tideworks_share_spider import TideworksShareSpider, CompanyInfo


class TerminalTideworksNolSpider(TideworksShareSpider):
    firms_code = "Q795"
    name = "terminal_tideworks_nol_multi"
    company_info = CompanyInfo(
        lower_short="nol",
        upper_short="NOL",
        email="tk@hardcoretech.co",
        password="Hardc0re",
    )
