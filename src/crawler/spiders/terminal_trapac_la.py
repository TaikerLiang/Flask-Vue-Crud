from crawler.core_terminal.trapac_share_spider import TrapacShareSpider, CompanyInfo


class TerminalTrapacLASpider(TrapacShareSpider):
    name = 'terminal_trapac_la'
    company_info = CompanyInfo(
        upper_short='LAX',
        lower_short='laz',
        email='',
        password='',
    )
