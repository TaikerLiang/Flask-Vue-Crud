from crawler.core_terminal.trapac_share_spider import TrapacShareSpider, CompanyInfo


class TerminalTrapacLASpider(TrapacShareSpider):
    name = 'terminal_trapac_jacksonville_multi'
    company_info = CompanyInfo(
        upper_short='JAX',
        lower_short='jax',
        email='',
        password='',
    )
