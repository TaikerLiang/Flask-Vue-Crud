from crawler.core_terminal.trapac_share_spider import TrapacShareSpider, CompanyInfo


class TerminalTrapacJackSpider(TrapacShareSpider):
    firms_code = 'M029'
    name = 'terminal_trapac_jacksonville'
    company_info = CompanyInfo(
        upper_short='JAX',
        lower_short='jacksonville',
        email='',
        password='',
    )
