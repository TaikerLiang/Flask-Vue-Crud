from crawler.core_terminal.trapac_share_spider import TrapacShareSpider, CompanyInfo


class TerminalTrapacOakSpider(TrapacShareSpider):
    firms_code = 'Y549'
    name = 'terminal_trapac_oakland'
    company_info = CompanyInfo(
        upper_short='OAK',
        lower_short='oakland',
        email='',
        password='',
    )
