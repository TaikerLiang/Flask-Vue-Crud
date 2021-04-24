from crawler.core_terminal.trapac_share_spider import TrapacShareSpider, CompanyInfo


class TerminalTrapacLASpider(TrapacShareSpider):
    name = 'terminal_trapac_oakland_multi'
    company_info = CompanyInfo(
        upper_short='OAK',
        lower_short='oak',
        email='',
        password='',
    )
