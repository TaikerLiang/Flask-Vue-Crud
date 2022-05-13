from crawler.core_terminal.trapac_share_spider import CompanyInfo, TrapacShareSpider


class TerminalTrapacJackSpider(TrapacShareSpider):
    firms_code = "M029"
    name = "terminal_m029_multi"
    company_info = CompanyInfo(
        upper_short="JAX",
        lower_short="jacksonville",
        email="",
        password="",
    )
