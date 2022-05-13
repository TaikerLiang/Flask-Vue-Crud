from crawler.core_terminal.trapac_share_spider import CompanyInfo, TrapacShareSpider


class TerminalTrapacOakSpider(TrapacShareSpider):
    firms_code = "Y549"
    name = "terminal_y549_multi"
    company_info = CompanyInfo(
        upper_short="OAK",
        lower_short="oakland",
        email="",
        password="",
    )
