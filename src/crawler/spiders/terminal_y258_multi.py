from crawler.core_terminal.trapac_share_spider import CompanyInfo, TrapacShareSpider


class TerminalTrapacLASpider(TrapacShareSpider):
    firms_code = "Y258"
    name = "terminal_y258_multi"
    company_info = CompanyInfo(
        upper_short="LAX",
        lower_short="losangeles",
        email="",
        password="",
    )
